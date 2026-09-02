"""The commons BYO wire (D-075) — the third and last protocol the park speaks.

The load-bearing claim, same as for the other two wires: **a wired leg is byte-identical to an
in-process one**. Everything else here exists to protect that claim from the specific ways a
turn-loop wire can break it — a mis-timed re-seed, a trimmed history, a transport that rejects a
legitimately bad answer, or a stale honesty report.

Ordered from cheapest to most expensive: serialization, then the parity matrix, then the HTTP
surface, then the sweep's social axis.
"""

from __future__ import annotations

import json
import urllib.error
import urllib.request

import pytest

from parkbench import cli
from parkbench.axis import RideResult
from parkbench.byo import NO_WIRE_RIDES, run_byo_commons, run_byo_profile
from parkbench.commons import make_agent
from parkbench.commons.scenario import generate_scenario
from parkbench.commons_client import drive_commons_agent
from parkbench.commons_protocol import (
    COMMONS_AXIS,
    COMMONS_RIDE,
    COMMONS_TASK,
    answer_spec,
    contribution_from_dict,
    history_from_list,
    history_to_list,
    scenario_from_dict,
    scenario_to_dict,
)
from parkbench.commons_server import CommonsParkServer
from parkbench.radar import build_radar
from parkbench.rides import RIDE_REGISTRY

AGENTS = ("random", "greedy", "heuristic", "optimal")


# --- serialization ----------------------------------------------------------------------------


@pytest.mark.parametrize("seed", [1, 2, 7])
def test_scenario_round_trips_through_json_unchanged(seed):
    """`from_dict(to_dict(s)) == s` is a real equality: the scenario is a frozen dataclass of scalars."""
    scenario = generate_scenario(seed)
    assert scenario_from_dict(json.loads(json.dumps(scenario_to_dict(scenario)))) == scenario


def test_the_derived_properties_survive_the_round_trip():
    """`threshold` and `levels` are recomputed, not transported — the two ends cannot disagree."""
    scenario = generate_scenario(3)
    rebuilt = scenario_from_dict(scenario_to_dict(scenario))
    assert rebuilt.threshold == scenario.threshold
    assert rebuilt.levels == scenario.levels
    # And they are genuinely absent from the wire form, so there is nothing to fall out of sync.
    assert "threshold" not in scenario_to_dict(scenario)


def test_history_round_trips_as_tuples_of_every_players_contribution():
    history = [(4, 8, 8, 0), (0, 8, 0, 0)]
    assert history_from_list(json.loads(json.dumps(history_to_list(history)))) == history


def test_the_answer_spec_describes_the_contribution_the_ride_expects():
    scenario = generate_scenario(1)
    spec = answer_spec(scenario)
    assert spec["kind"] == "contribution"
    assert spec["range"] == [0, scenario.endowment]
    assert spec["levels"] == list(scenario.levels)


def test_contribution_parsing_accepts_integers_and_rejects_everything_else():
    assert contribution_from_dict({"contribution": 0}) == 0
    assert contribution_from_dict({"contribution": 5}) == 5
    # Out of range is *accepted* here and clamped by the ride — see the malformed-answer test below.
    assert contribution_from_dict({"contribution": -3}) == -3
    for bad in ({}, {"contribution": "4"}, {"contribution": 4.5}, {"contribution": True}):
        with pytest.raises(ValueError):
            contribution_from_dict(bad)


# --- the load-bearing claim: wired == in-process -----------------------------------------------


@pytest.mark.parametrize("agent_name", AGENTS)
def test_a_wired_leg_matches_the_in_process_ride(agent_name):
    """Every baseline, over a socket, scores exactly what it scores in-process — `detail` included.

    `random` is in this matrix on purpose. It is the only baseline whose score depends on the
    re-seed, so it is the only one that can catch a `new_game` sent at the wrong moment — and the
    failure mode there is a plausible-looking wrong number, not a crash.
    """
    wired, leg = run_byo_commons(make_agent(agent_name), seed=1, byo_name=agent_name)
    in_process = RIDE_REGISTRY[COMMONS_RIDE].evaluate(agent_name, 1)

    assert wired == in_process
    assert leg["ride"] == COMMONS_RIDE and leg["wire"] == "commons" and leg["task"] == COMMONS_TASK
    assert leg["games"] == 12
    assert leg["rounds"] > leg["games"]  # a turn wire answers several times per scored unit


def test_the_agent_seam_leaves_the_registry_path_untouched():
    """`evaluate(x, s)` and `evaluate(x, s, agent=None)` must be the same call (the seam is inert)."""
    for agent_name in AGENTS:
        assert RIDE_REGISTRY[COMMONS_RIDE].evaluate(agent_name, 1) == RIDE_REGISTRY[
            COMMONS_RIDE
        ].evaluate(agent_name, 1, agent=None)


def test_new_game_arrives_once_per_game_on_round_zero():
    """The re-seed hop: once per game, never mid-game.

    A wire that re-seeded every round would restart the RNG inside a game. `random`'s parity above
    would catch that, but only as a number — this pins the mechanism, so the reason a future change
    breaks parity is readable from the failure.
    """
    seen = []

    class _Recorder:
        """Wraps a real agent and records the (round_idx, was_reset) sequence it was driven with."""

        def __init__(self, inner):
            self.inner = inner
            self._reset_pending = False

        def reset(self, seed=0):
            self._reset_pending = True
            self.inner.reset(seed=seed)

        def contribute(self, round_idx, history, scenario):
            seen.append((round_idx, self._reset_pending))
            self._reset_pending = False
            return self.inner.contribute(round_idx, history, scenario)

    server = CommonsParkServer(seed=1, agent_name="recorder").start()
    try:
        drive_commons_agent(server.base_url, _Recorder(make_agent("heuristic")))
        server.wait(timeout=60)
    finally:
        server.stop()

    assert seen, "the recorder was never asked to contribute"
    # A reset is observed exactly on the rounds that open a game, and on no others.
    assert all(was_reset == (round_idx == 0) for round_idx, was_reset in seen)
    assert sum(1 for _, was_reset in seen if was_reset) == 12


def test_the_history_carries_the_whole_society_not_just_the_agents_own_past():
    """The cast's contributions are the social signal the ride scores — trimming them scores the ride.

    The house contains a grim-trigger reciprocator. An agent that cannot see it cannot condition on
    it, so a summarised or self-only history would quietly turn a reciprocity game into a solo one.
    """
    captured = []

    class _Watcher:
        def reset(self, seed=0):
            pass

        def contribute(self, round_idx, history, scenario):
            captured.append((round_idx, history, scenario))
            return scenario.threshold  # meet the bar, so the reciprocator keeps cooperating

    server = CommonsParkServer(seed=1, agent_name="watcher").start()
    try:
        drive_commons_agent(server.base_url, _Watcher())
        server.wait(timeout=60)
    finally:
        server.stop()

    later = [(r, h, s) for r, h, s in captured if r > 0]
    assert later, "no round after the first was observed"
    for round_idx, history, scenario in later:
        assert len(history) == round_idx  # one row per completed round
        for row in history:
            assert len(row) == scenario.n_players  # the agent AND every house member
    # And the reciprocator is visibly reacting: someone other than the agent contributed.
    assert any(any(row[1:]) for _r, h, _s in later for row in h)


# --- the HTTP surface -------------------------------------------------------------------------


def _get(url: str) -> dict:
    with urllib.request.urlopen(url, timeout=10) as resp:
        return json.loads(resp.read().decode("utf-8"))


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
    """One hand-rolled turn against the documented endpoints — no reference client involved."""
    server = CommonsParkServer(seed=1, agent_name="hand-rolled").start()
    try:
        health = _get(f"{server.base_url}/health")
        assert health == {"status": "ok", "ride": COMMONS_RIDE, "agent": "hand-rolled"}

        state = _get(f"{server.base_url}/observation")
        while state.get("status") == "waiting":
            state = _get(f"{server.base_url}/observation")
        assert state["status"] == "your_turn"
        assert state["ride"] == COMMONS_RIDE and state["task"] == COMMONS_TASK
        assert state["round_idx"] == 0 and state["history"] == []
        assert state["new_game"]["seed"] == 1 * 1_000_003 + 0  # the suite's own per-game reset
        assert set(state["scenario"]) >= {"n_players", "n_rounds", "endowment", "multiplier", "cast"}

        status, body = _post(f"{server.base_url}/contribution", {"contribution": 0})
        assert status == 200 and body == {"status": "accepted", "step": 1}
    finally:
        server.stop()


def test_posting_out_of_turn_is_a_409_and_a_bad_body_is_a_400():
    server = CommonsParkServer(seed=1).start()
    try:
        drive_commons_agent(server.base_url, make_agent("heuristic"))
        server.wait(timeout=60)
        assert _post(f"{server.base_url}/contribution", {"contribution": 1})[0] == 409
        assert _post(f"{server.base_url}/contribution", {"contribution": "1"})[0] == 400
    finally:
        server.stop()


def test_an_unknown_path_is_a_404():
    server = CommonsParkServer(seed=1).start()
    try:
        with pytest.raises(urllib.error.HTTPError) as exc:
            _get(f"{server.base_url}/plan")
        assert exc.value.code == 404
    finally:
        server.stop()


def test_a_malformed_answer_is_priced_by_the_ride_not_rejected_by_the_transport():
    """Free-riding and out-of-range numbers are answers, not protocol errors.

    Contributing 0 forever is legal free-riding; the reciprocator punishes it and the score falls.
    A wildly out-of-range number is clamped by the ride exactly as it is for a built-in agent. If the
    transport rejected either with a 400, a real failure would hide behind an HTTP error and a BYO
    score would be quietly inflated.
    """

    class _Absurd:
        def reset(self, seed=0):
            pass

        def contribute(self, round_idx, history, scenario):
            return 10_000  # far past the endowment

    server = CommonsParkServer(seed=1, agent_name="absurd").start()
    try:
        drive_commons_agent(server.base_url, _Absurd())
        result = server.wait(timeout=60)
    finally:
        server.stop()

    assert isinstance(result, RideResult)
    assert 0.0 <= result.score <= 1.0
    # Clamped to a full contribution every round, which is over-paying, not cheating: scored, not 400.
    assert result.detail["cooperation_rate"] == 1.0


# --- the sweep --------------------------------------------------------------------------------


def test_the_commons_wire_completes_the_social_axis():
    """The D-075 headline. Before this lap a swept `social` was one ride; now it is the same two."""
    swept = run_byo_profile("heuristic", seed=1)
    baseline = build_radar("heuristic", seed=1)

    assert swept.profile.axis_scores["social"] == baseline.axis_scores["social"]
    assert [r.ride for r in swept.profile.results][:2] == ["negotiation", "commons"]
    assert "commons" not in swept.profile.skipped


def test_commons_is_no_longer_reported_as_unreachable():
    """The honesty report must not keep claiming a ride is out of reach after it has been scored."""
    run = run_byo_profile("heuristic", seed=1, n_scenarios=2)
    assert set(run.wire["unreachable"]) == set(NO_WIRE_RIDES) == {"coding"}
    assert "commons" not in run.wire["unreachable"]
    assert "commons" in [leg["ride"] for leg in run.wire["rides"]]


def test_a_commons_only_sweep_reports_a_partial_social_axis():
    """One social ride is still an honest half-axis — narrower than a baseline's, and it says so."""
    run = run_byo_profile("optimal", seed=1, rides=("commons",))
    assert [r.ride for r in run.profile.results] == ["commons"]
    assert run.profile.covered_axes == ["social"]
    assert "negotiation" in run.profile.skipped
    assert run.profile.axis_scores["social"] == 1.0  # the ceiling, by construction


def test_a_commons_leg_is_deterministic_and_carries_no_clock_or_port():
    a = json.dumps(run_byo_profile("greedy", seed=1, rides=("commons",)).to_dict(), sort_keys=True)
    b = json.dumps(run_byo_profile("greedy", seed=1, rides=("commons",)).to_dict(), sort_keys=True)
    assert a == b
    for leak in ("timestamp", "port", "127.0.0.1", "elapsed", "duration"):
        assert leak not in a


# --- the CLI surface --------------------------------------------------------------------------


def test_cli_serve_ride_commons_drives_the_wire_in_process(capsys):
    assert cli.main(["serve", "--ride", "commons", "--port", "0", "--local-agent", "optimal"]) in (
        None,
        0,
    )
    out = capsys.readouterr().out
    assert "GET  /observation   POST /contribution" in out
    assert f"axis={COMMONS_AXIS}" in out
    assert "commons score: 1.000000" in out


def test_cli_byo_run_can_select_the_commons_wire_alone(capsys):
    assert cli.main(["byo-run", "--rides", "commons", "--json"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert [r["ride"] for r in payload["rides"]] == ["commons"]
    assert list(payload["axes"]) == ["social"]
    assert payload["missing_axes"] == ["economic", "coding", "safety"]
