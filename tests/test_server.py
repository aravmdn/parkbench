"""The HTTP/JSON server slice (decision D-027).

The central claim: driving the test agent (side A) over the wire produces the *exact* same
profile as the pure in-process run. That parity is what lets a bring-your-own agent be scored
without bespoke glue while preserving the reproducibility the whole project rests on.

Everything here runs in-process on an ephemeral port (`port=0`); no external network.
"""

import json
import threading
import urllib.request

from parkbench.agents import make_agent
from parkbench.client import drive_agent
from parkbench.protocol import Action, Observation, Offer
from parkbench.server import (
    ParkServer,
    action_from_dict,
    observation_from_dict,
    observation_to_dict,
)
from parkbench.suite import Suite, run_suite


def _signature(profile):
    """Same byte-for-byte profile signature the determinism tests use."""
    return (
        round(profile.efficiency.mean, 9),
        round(profile.own_value.mean, 9),
        round(profile.deal_rate, 9),
        tuple(
            sorted(
                (p, round(v["efficiency"].mean, 9), round(v["own_value"].mean, 9))
                for p, v in profile.per_persona.items()
            )
        ),
    )


# --- serialisation round-trips ------------------------------------------------------------


def test_observation_roundtrip_preserves_values():
    obs = Observation(
        role="A",
        my_util=((10.0, 20.0, 30.0), (5.0, 0.0, 1.0)),
        standing_offer=Offer((1, 2)),
        my_last_offer=None,
        rounds_left=4,
        history=({"party": "B", "type": "offer", "offer": {"levels": [0, 0]}, "message": "hi"},),
    )
    back = observation_from_dict(observation_to_dict(obs))
    assert back == obs


def test_action_roundtrip_preserves_values():
    for action in (
        Action.make_offer(Offer((0, 1, 2)), "take it"),
        Action.accept("deal"),
        Action.say("hello"),
    ):
        back = action_from_dict(action.to_dict())
        assert back.type == action.type
        assert back.offer == action.offer
        assert back.message == action.message


# --- end-to-end parity --------------------------------------------------------------------


def test_http_run_matches_in_process_run():
    """Drive a local heuristic agent over HTTP; the profile must equal the in-process run."""
    suite = Suite(seed=1, n_scenarios=6)

    # Reference: the ordinary in-process run.
    ref_profile, _ = run_suite(suite, make_agent("heuristic"))

    # Over the wire: park hosts the run on an ephemeral port, client drives the same agent.
    server = ParkServer(suite, host="127.0.0.1", port=0, agent_name="heuristic", write_log=False)
    server.start()
    try:
        drive_agent(server.base_url, make_agent("heuristic"))
        http_profile, _ = server.wait(timeout=30)
    finally:
        server.stop()

    assert _signature(http_profile) == _signature(ref_profile)
    # The wire run is labelled by the server's agent_name, not the driving client.
    assert http_profile.agent_name == "heuristic"


def test_http_run_matches_in_process_run_random_agent():
    """A seed-dependent agent (random) must also reach parity via per-match re-seeding."""
    suite = Suite(seed=2, n_scenarios=6)
    ref_profile, _ = run_suite(suite, make_agent("random"))

    server = ParkServer(suite, host="127.0.0.1", port=0, agent_name="random", write_log=False)
    server.start()
    try:
        drive_agent(server.base_url, make_agent("random"))
        http_profile, _ = server.wait(timeout=30)
    finally:
        server.stop()

    assert _signature(http_profile) == _signature(ref_profile)


def test_health_endpoint():
    suite = Suite(seed=1, n_scenarios=1)
    server = ParkServer(suite, host="127.0.0.1", port=0, agent_name="byo", write_log=False)
    server.start()
    try:
        with urllib.request.urlopen(f"{server.base_url}/health", timeout=10) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
        assert payload["status"] == "ok"
        assert payload["agent"] == "byo"
        # Drain the run so the daemon threads finish cleanly.
        drive_agent(server.base_url, make_agent("heuristic"))
        server.wait(timeout=30)
    finally:
        server.stop()


def test_done_status_reported_after_run():
    """After the run finishes, /observation reports status 'done' with the profile."""
    suite = Suite(seed=1, n_scenarios=1)
    server = ParkServer(suite, host="127.0.0.1", port=0, agent_name="heuristic", write_log=False)
    server.start()
    try:
        final = drive_agent(server.base_url, make_agent("heuristic"))
        server.wait(timeout=30)
    finally:
        server.stop()
    assert final["status"] == "done"
    assert final["profile"]["agent"] == "heuristic"
    assert final["profile"]["efficiency"]["n"] == 1 * 4  # 1 scenario x 4 personas


def test_concurrent_runs_on_distinct_ports():
    """Two servers can host independent runs simultaneously without interfering."""
    suite = Suite(seed=1, n_scenarios=3)
    ref, _ = run_suite(suite, make_agent("heuristic"))

    results = {}

    def _run(key):
        srv = ParkServer(suite, host="127.0.0.1", port=0, agent_name="heuristic", write_log=False)
        srv.start()
        try:
            drive_agent(srv.base_url, make_agent("heuristic"))
            prof, _ = srv.wait(timeout=30)
            results[key] = _signature(prof)
        finally:
            srv.stop()

    threads = [threading.Thread(target=_run, args=(k,)) for k in ("a", "b")]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=60)

    assert results["a"] == _signature(ref)
    assert results["b"] == _signature(ref)
