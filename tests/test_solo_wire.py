"""The solo-ride BYO wire (D-074) — scenario out, plan back, for the four plan-shaped rides.

The central claim is the same one D-073 made for negotiation, now for four more rides: an agent
driven over the **real** HTTP wire earns exactly the score the in-process ride gives it, ``detail``
included — so a third party can finally be measured on the economic and safety axes rather than on
the social axis alone. The second claim is still honesty: two rides have no wire, and a captured
profile says so by name instead of quietly reading as a complete one.

Everything runs in-process on an ephemeral loopback port (``port=0``); no external network.
"""

from __future__ import annotations

import json
import urllib.error
import urllib.request

import pytest

from parkbench import BENCHMARK_VERSION, cli
from parkbench.axis import RideResult
from parkbench.byo import NO_WIRE_RIDES, run_byo_profile, run_byo_solo
from parkbench.radar import build_radar
from parkbench.rides import RIDE_REGISTRY
from parkbench.solo_client import drive_solo_agent
from parkbench.solo_protocol import (
    SOLO_RIDES,
    UNREACHABLE_RIDES,
    answer_spec,
    plan_from_dict,
    scenario_from_dict,
    scenario_to_dict,
    spec_for,
)
from parkbench.solo_server import SoloParkServer

BASELINES = ("random", "greedy", "heuristic", "optimal")


def _ride_agent(ride: str, agent_name: str):
    """The ``ride``-roster agent object (each ride owns its own interface, D-035)."""
    from importlib import import_module

    return import_module(f"parkbench.{ride}").make_agent(agent_name)


def _scenarios(ride: str, seed: int = 1, n: int = 3):
    from importlib import import_module

    return import_module(f"parkbench.{ride}.suite").build_scenarios(seed, n)


# --- the serialization round-trips exactly -------------------------------------------------


@pytest.mark.parametrize("ride", sorted(SOLO_RIDES))
def test_scenario_round_trips_through_json_unchanged(ride):
    """`from_dict(to_dict(s)) == s`, through real JSON — the wire loses nothing about the task.

    Scenarios are frozen dataclasses of plain integers, so this is a true equality rather than a
    field-by-field spot check: a transported instance IS the instance the ride generated.
    """
    for scenario in _scenarios(ride, seed=7, n=4):
        payload = json.loads(json.dumps(scenario_to_dict(ride, scenario)))
        assert scenario_from_dict(ride, payload) == scenario


@pytest.mark.parametrize("ride", sorted(SOLO_RIDES))
def test_answer_spec_describes_the_plan_the_ride_expects(ride):
    scenario = _scenarios(ride, seed=3, n=1)[0]
    spec = answer_spec(ride, scenario)
    assert spec["kind"] and spec["note"]
    optimal = tuple(_ride_agent(ride, "optimal").choose(scenario))
    if spec["length"] is not None:
        # Fixed-length answers (permutation / one index per round or cycle): the ride's own optimal
        # play must satisfy the length the wire advertises, or the advertisement is wrong.
        assert spec["length"] == len(optimal)


def test_an_injection_is_transported_verbatim_lie_included():
    """The adversarial nudge must survive the wire — filtering it would score the safety ride."""
    injected = [
        s for s in _scenarios("safety", seed=1, n=12) if any(r.injection for r in s.rounds)
    ]
    assert injected, "the safety suite should contain injected scenarios"
    for scenario in injected:
        payload = scenario_to_dict("safety", scenario)
        claims = [r["injection"] for r in payload["rounds"] if r["injection"]]
        assert claims
        assert scenario_from_dict("safety", payload) == scenario


def test_plan_parsing_accepts_indices_and_rejects_non_indices():
    assert plan_from_dict({"plan": [0, 2, 1]}) == (0, 2, 1)
    assert plan_from_dict({"plan": []}) == ()
    for bad in ({}, {"plan": "012"}, {"plan": [0, "1"]}, {"plan": [0, 1.5]}, {"plan": [True]}):
        with pytest.raises(ValueError):
            plan_from_dict(bad)


def test_a_ride_without_a_wire_is_refused_by_name():
    for ride in UNREACHABLE_RIDES:
        with pytest.raises(ValueError) as exc:
            spec_for(ride)
        assert ride in str(exc.value)
        # The refusal names what the wire *does* carry, so the caller learns the boundary.
        assert "economic" in str(exc.value)


# --- the load-bearing claim: wired == in-process --------------------------------------------


@pytest.mark.parametrize("ride", sorted(SOLO_RIDES))
@pytest.mark.parametrize("agent_name", BASELINES)
def test_wired_leg_matches_the_in_process_ride(ride, agent_name):
    """A run over the socket == the same agent's in-process ride result, detail for detail.

    This is what makes a live BYO leg comparable to a baseline's: the connector transports, and the
    ride scores. Run for every baseline because `random` is seed-dependent — parity there is what
    proves the `new_scenario` re-seed hop reproduces the in-process suite exactly.
    """
    wired, leg = run_byo_solo(ride, _ride_agent(ride, agent_name), seed=1)
    in_process = RIDE_REGISTRY[ride].evaluate(agent_name, 1)

    assert wired.score == in_process.score
    assert wired.detail == in_process.detail
    assert wired.ride == ride
    assert wired.axis == in_process.axis
    assert leg["steps"] == in_process.detail["n_scenarios"]


def test_the_agent_seam_leaves_the_registry_path_untouched():
    """`evaluate(..., agent=None)` must be the exact call the radar has always made."""
    for ride in sorted(SOLO_RIDES):
        assert RIDE_REGISTRY[ride].evaluate("heuristic", 1) == RIDE_REGISTRY[ride].evaluate(
            "heuristic", 1, agent=None
        )


def test_a_malformed_plan_is_scored_by_the_ride_not_rejected_by_the_transport():
    """A well-formed-but-wrong plan must reach the ride and score 0 there.

    The transport deliberately does not validate plan *content*: an over-budget knapsack pick is a
    real failure the ride prices at 0, and turning it into an HTTP error would hide it — inflating
    a BYO agent's score by silently dropping its worst answers.
    """

    class TakeEverything:
        """Answers every knapsack scenario with all items — always over budget."""

        name = "take-everything"

        def reset(self, seed: int = 0) -> None:
            pass

        def choose(self, scenario):
            return tuple(range(scenario.n_items))

    result, _leg = run_byo_solo("economic", TakeEverything(), seed=1)
    assert result.score == 0.0
    assert result.detail["feasible_rate"] == 0.0
    # And the ride's integrity signal reports the breach, so a career would price it (D-041).
    assert result.detail["integrity"] == 0.0


# --- the HTTP surface itself -----------------------------------------------------------------


def _get(url: str) -> tuple[int, dict]:
    try:
        with urllib.request.urlopen(url, timeout=10) as resp:
            return resp.status, json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        return exc.code, json.loads(exc.read().decode("utf-8"))


def _post(url: str, payload: dict) -> tuple[int, dict]:
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url, data=data, method="POST", headers={"Content-Type": "application/json"}
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return resp.status, json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        return exc.code, json.loads(exc.read().decode("utf-8"))


def test_the_wire_speaks_the_documented_shapes():
    """/health, a scenario hand-out, an accepted plan, and the final result — over a real socket."""
    server = SoloParkServer("exchange", seed=2, agent_name="wire-bot").start()
    try:
        code, health = _get(f"{server.base_url}/health")
        assert (code, health["status"], health["ride"]) == (200, "ok", "exchange")
        assert health["agent"] == "wire-bot"

        # Unknown routes and methods are refused the same way the negotiation wire refuses them.
        assert _get(f"{server.base_url}/nope")[0] == 404
        assert _post(f"{server.base_url}/nope", {})[0] == 404

        agent = _ride_agent("exchange", "heuristic")
        first = None
        while True:
            code, state = _get(f"{server.base_url}/scenario")
            assert code == 200
            if state["status"] == "done":
                break
            if state["status"] != "your_turn":
                continue
            if first is None:
                first = state
            agent.reset(seed=int(state["new_scenario"]["seed"]))
            scenario = scenario_from_dict(state["ride"], state["scenario"])
            code, ack = _post(
                f"{server.base_url}/plan", {"plan": [int(i) for i in agent.choose(scenario)]}
            )
            assert (code, ack["status"]) == (200, "accepted")
            assert ack["step"] == state["step"]

        assert first["step"] == 1
        assert first["ride"] == "exchange"
        assert first["task"] == "assignment"
        assert first["answer"]["kind"] == "permutation"
        assert isinstance(first["new_scenario"]["seed"], int)

        result = state["result"]
        assert result["ride"] == "exchange"
        assert result["axis"] == "economic"
        assert result["score"] == RIDE_REGISTRY["exchange"].evaluate("heuristic", 2).score
    finally:
        server.stop()


def test_posting_a_plan_out_of_turn_is_a_409_and_a_bad_body_is_a_400():
    server = SoloParkServer("economic", seed=1).start()
    try:
        # Drain the run first so nothing is pending, then post into the void.
        drive_solo_agent(server.base_url, _ride_agent("economic", "heuristic"))
        assert _post(f"{server.base_url}/plan", {"plan": [0]})[0] == 409
        assert _post(f"{server.base_url}/plan", {"plan": "nope"})[0] == 400
    finally:
        server.stop()


def test_a_ride_without_a_wire_cannot_be_hosted():
    for ride in UNREACHABLE_RIDES:
        with pytest.raises(ValueError):
            SoloParkServer(ride)


# --- the multi-wire sweep --------------------------------------------------------------------


def test_a_full_sweep_covers_three_axes_and_names_what_it_cannot_reach():
    """The D-075 headline: three axes live, `coding` honestly missing, the one wireless ride named."""
    run = run_byo_profile("heuristic", seed=1, byo_name="acme-bot")

    assert run.profile.covered_axes == ["social", "economic", "safety"]
    assert run.profile.missing_axes == ["coding"]
    assert run.profile.skipped == ["coding"]
    # Registry order, minus the one ride no wire carries.
    assert [r.ride for r in run.profile.results] == [
        "negotiation",
        "commons",
        "economic",
        "exchange",
        "safety",
        "containment",
    ]
    assert all(r.agent == "acme-bot" for r in run.profile.results)


def test_every_swept_axis_equals_the_in_process_axis_exactly():
    """D-075 removes the last asymmetry: every axis a wire reaches is now *complete*.

    Until this lap `social` was the odd one out — one ride over the wire where a baseline got the
    mean of two — and the test asserted that gap rather than glossing it. With the commons wire the
    gap is gone, so the claim gets stronger: for all three reachable axes a swept BYO profile and a
    baseline radar agree to the last digit. `coding` is still not reachable at all, which is a
    missing axis, not a partial one.
    """
    swept = run_byo_profile("heuristic", seed=1)
    baseline = build_radar("heuristic", seed=1)

    for axis in ("social", "economic", "safety"):
        assert swept.profile.axis_scores[axis] == baseline.axis_scores[axis]
    assert swept.profile.axis_scores["social"] == (
        RIDE_REGISTRY["negotiation"].evaluate("heuristic", 1).score
        + RIDE_REGISTRY["commons"].evaluate("heuristic", 1).score
    ) / 2
    assert "coding" not in swept.profile.axis_scores


def test_a_sweep_is_deterministic_and_carries_no_clock_or_port():
    """Same agent, same seed => byte-identical JSON, exactly like every other Parkbench result."""
    a = json.dumps(run_byo_profile("greedy", seed=1, n_scenarios=2).to_dict(), sort_keys=True)
    b = json.dumps(run_byo_profile("greedy", seed=1, n_scenarios=2).to_dict(), sort_keys=True)
    assert a == b
    for leak in ("timestamp", "port", "127.0.0.1", "elapsed", "duration"):
        assert leak not in a


def test_a_sweep_can_be_narrowed_to_a_subset_of_wires():
    run = run_byo_profile("heuristic", seed=1, n_scenarios=2, rides=("safety", "containment"))
    assert [r.ride for r in run.profile.results] == ["safety", "containment"]
    assert run.profile.covered_axes == ["safety"]
    # Rides not driven are skipped alongside the one with no wire — the list is what was NOT scored,
    # which is a superset of what *could* not be scored.
    assert "economic" in run.profile.skipped and "commons" in run.profile.skipped


def test_a_solo_only_sweep_works_for_an_agent_the_negotiation_roster_lacks():
    """`optimal` exists on every solo ride and on no negotiation cast — driving it must not crash.

    It is the live case for the identity fallback: the solo agent classes predate D-038 and have no
    `identity()`, so a sweep that never touches the negotiation wire has to derive one another way.
    """
    run = run_byo_profile("optimal", seed=1, rides=tuple(sorted(SOLO_RIDES)))
    assert run.profile.covered_axes == ["economic", "safety"]
    assert all(r.score == 1.0 for r in run.profile.results)  # the ceiling, by construction
    assert run.identity.config_hash  # deterministic, and distinct per driver
    assert run.identity.config_hash != run_byo_profile(
        "greedy", seed=1, rides=("economic",)
    ).identity.config_hash


def test_a_roster_mismatch_fails_by_name_before_any_socket_is_bound():
    """Rosters differ per ride (D-035), so "which agent" is only answerable per ride.

    `optimal` exists on every solo ride and on no negotiation cast, so this combination is a real
    user error — it should say which ride refused and not surface a bare registry `KeyError` half a
    sweep in.
    """
    with pytest.raises(ValueError) as exc:
        run_byo_profile("optimal", seed=1, rides=("negotiation", "economic"))
    assert "negotiation" in str(exc.value) and "optimal" in str(exc.value)


def test_the_sweep_records_its_own_wire_traffic():
    run = run_byo_profile("heuristic", seed=1, n_scenarios=2)
    wire = run.to_dict()["source"]
    assert wire["mode"] == "live"
    assert wire["protocol"] == "http/json"
    assert wire["spec"] == "docs/09-byo-protocol.md"
    assert [leg["ride"] for leg in wire["rides"]] == [r.ride for r in run.profile.results]
    # 2 negotiation scenarios x 4 personas + 12 commons games + 4 solo rides x 12 scenarios.
    assert wire["matches"] == 8 + 12 + 4 * 12
    assert wire["turns"] > wire["matches"]
    # A commons leg reports games and rounds separately, because on a turn wire they differ.
    commons_leg = next(leg for leg in wire["rides"] if leg["ride"] == "commons")
    assert commons_leg["games"] == 12 and commons_leg["rounds"] > commons_leg["games"]
    # What a profile reports as out of reach is the rides with NO wire — not the plan wire's own
    # limits, which still (correctly) list `commons`.
    assert set(wire["unreachable"]) == set(NO_WIRE_RIDES) == {"coding"}
    assert "commons" in UNREACHABLE_RIDES  # unreachable by *this* wire, reachable by its own


def test_a_sweep_still_earns_no_career():
    """A three-axis agent is closer to a full profile but still has no career (D-041).

    A career multiplies an integrity signal from *every* ride; one ride still has no wire, so the
    product does not exist. Being nearly-complete must not quietly promote a BYO agent onto the
    leaderboard — one missing factor is as disqualifying as two.
    """
    run = run_byo_profile("heuristic", seed=1, n_scenarios=2)
    assert run.profile.skipped, "a BYO sweep must still report unscored rides"
    assert "coding" in run.profile.missing_axes


# --- the CLI + endpoint surfaces --------------------------------------------------------------


def test_cli_byo_run_defaults_to_the_single_negotiation_leg(capsys):
    """`--rides` defaults to the D-073 behaviour, so the committed BYO payload shape is unchanged."""
    assert cli.main(["byo-run", "--json", "--scenarios", "2"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert [r["ride"] for r in payload["rides"]] == ["negotiation"]
    assert payload["missing_axes"] == ["economic", "coding", "safety"]


def test_cli_byo_run_all_sweeps_every_wire(capsys):
    assert cli.main(["byo-run", "--rides", "all", "--json", "--scenarios", "2"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert list(payload["axes"]) == ["social", "economic", "safety"]
    assert payload["missing_axes"] == ["coding"]
    assert payload["live"] is True and payload["byo"] is True


def test_cli_byo_run_text_output_lists_every_leg(capsys):
    assert cli.main(["byo-run", "--rides", "all", "--scenarios", "2"]) == 0
    text = capsys.readouterr().out
    for ride in ("negotiation", "commons", "economic", "exchange", "safety", "containment"):
        assert ride in text
    assert "no wire carries:" in text
    assert "docs/09-byo-protocol.md" in text


def test_the_byo_endpoint_can_serve_a_full_sweep():
    """`/byo?rides=all` returns the same payload the CLI prints, stamped (D-067 parity rule)."""
    from parkbench.profiles_server import build_byo_payload

    served = build_byo_payload(driver="heuristic", seed=1, n_scenarios=2, rides="all")
    assert served["benchmark_version"] == BENCHMARK_VERSION
    expected = run_byo_profile("heuristic", seed=1, n_scenarios=2).to_dict()
    assert {k: v for k, v in served.items() if k != "benchmark_version"} == expected


def test_the_byo_endpoint_refuses_an_unknown_rides_value():
    from parkbench.profiles_server import build_byo_payload

    with pytest.raises(ValueError):
        build_byo_payload(driver="heuristic", rides="negotiation,safety")


def test_every_registered_ride_is_on_a_wire_or_named_as_having_none():
    """A guard against a new ride being added to the park and quietly skipping the BYO surface.

    Every registered ride must be on the plan wire, the negotiation wire or the commons wire, or be
    named in `NO_WIRE_RIDES` with a reason. Adding a ride without doing one of those four fails here.
    """
    accounted = set(SOLO_RIDES) | {"negotiation", "commons"} | set(NO_WIRE_RIDES)
    assert set(RIDE_REGISTRY) <= accounted
    # And the two lists must not overlap: a ride cannot be both driven and reported unreachable.
    assert not (set(SOLO_RIDES) | {"negotiation", "commons"}) & set(NO_WIRE_RIDES)


def test_a_wired_result_is_a_real_ride_result():
    result, _leg = run_byo_solo("safety", _ride_agent("safety", "optimal"), seed=1)
    assert isinstance(result, RideResult)
    assert result.score == 1.0  # `optimal` is the ceiling by construction
