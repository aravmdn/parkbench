"""Nudge controls + off-record handling (decision D-029).

Covers: persona swap changes the counterpart (and the result), scenario injection runs a
supplied scenario, off_record is set correctly, and off-record matches are excluded from
canonical aggregation.
"""

import json

from parkbench.agents import make_agent
from parkbench.engine import MatchResult
from parkbench.nudge import Nudge, parse_scenario_spec, persona_class
from parkbench.protocol import Offer
from parkbench.scenario import Scenario, analyze
from parkbench.runlog import SCHEMA_VERSION, write_run
from parkbench.scoring import (
    build_off_record_profile,
    build_profile,
    score_match,
)
from parkbench.suite import Suite, run_suite


def _hand():
    sc = Scenario(("i0", "i1"), 2, (80.0, 20.0), (30.0, 70.0), 0)
    return sc, analyze(sc)


# --- persona swap -----------------------------------------------------------------------

def test_swap_persona_restricts_roster_to_one_counterpart():
    suite = Suite(seed=1, n_scenarios=3)
    nudge = Nudge(swap_persona="tough")
    profile, records = run_suite(suite, make_agent("heuristic"), nudge)
    # 3 scenarios x 1 persona (tough only) == 3 matches, and only tough appears.
    assert len(records) == 3
    assert {r["persona"] for r in records} == {"tough"}
    assert set(profile.per_persona) == {"tough"}


def test_swap_persona_changes_the_result():
    """Facing only `tough` should differ from facing only `cooperative`."""
    suite = Suite(seed=1, n_scenarios=6)
    tough, _ = run_suite(suite, make_agent("heuristic"), Nudge(swap_persona="tough"))
    coop, _ = run_suite(suite, make_agent("heuristic"), Nudge(swap_persona="cooperative"))
    # A good agent typically captures more of its own value against a cooperative counterpart.
    assert tough.own_value.mean != coop.own_value.mean


def test_unknown_persona_raises():
    try:
        persona_class("nope")
    except ValueError as e:
        assert "Unknown persona" in str(e)
    else:
        raise AssertionError("expected ValueError for unknown persona")


# --- scenario injection -----------------------------------------------------------------

def test_inject_scenario_runs_the_supplied_scenario():
    suite = Suite(seed=1, n_scenarios=12)  # would normally be 12 scenarios
    sc = parse_scenario_spec(
        '{"issues":["price","term"],"n_levels":3,"weight_a":[70,30],"weight_b":[40,60],"seed":777}'
    )
    nudge = Nudge(inject_scenario=sc)
    _, records = run_suite(suite, make_agent("heuristic"), nudge)
    # Exactly one scenario is run (against the full 4-persona cast) regardless of n_scenarios.
    assert len({r["scenario_seed"] for r in records}) == 1
    assert all(r["scenario_seed"] == 777 for r in records)
    assert len(records) == 4  # 1 scenario x 4 personas


def test_parse_scenario_spec_from_file(tmp_path):
    p = tmp_path / "scn.json"
    p.write_text(json.dumps({"n_levels": 3, "weight_a": [60, 40], "weight_b": [50, 50]}))
    sc = parse_scenario_spec(str(p))
    assert sc.n_issues == 2
    assert sc.issues == ("issue_0", "issue_1")  # default issue names
    assert sc.weight_a == (60.0, 40.0)


def test_parse_scenario_spec_rejects_bad_input():
    for bad in ('{"weight_a":[1,2]}', '{"weight_a":[1,2],"weight_b":[1]}', "not json"):
        try:
            parse_scenario_spec(bad)
        except ValueError:
            pass
        else:
            raise AssertionError(f"expected ValueError for {bad!r}")


# --- off-record flagging ----------------------------------------------------------------

def test_nudge_auto_sets_off_record():
    assert Nudge(swap_persona="tough").off_record is True
    assert Nudge(inject_scenario=_hand()[0]).off_record is True
    assert Nudge(force_off_record=True).off_record is True
    assert Nudge().off_record is False


def test_nudged_run_flags_records_and_profile_off_record():
    suite = Suite(seed=1, n_scenarios=2)
    profile, records = run_suite(suite, make_agent("heuristic"), Nudge(swap_persona="fair"))
    assert profile.off_record is True
    assert all(r["off_record"] is True for r in records)


def test_canonical_run_is_on_record():
    suite = Suite(seed=1, n_scenarios=2)
    profile, records = run_suite(suite, make_agent("heuristic"))
    assert profile.off_record is False
    assert all(r["off_record"] is False for r in records)
    assert profile.excluded == 0


# --- exclusion from canonical aggregation -----------------------------------------------

def test_off_record_matches_excluded_from_canonical_profile():
    sc, an = _hand()
    on = score_match(sc, an, MatchResult(True, Offer((1, 0)), [], 2, 8), "fair")
    off = score_match(
        sc, an, MatchResult(True, Offer((0, 1)), [], 2, 8), "tough", off_record=True
    )
    prof = build_profile("x", [on, off])
    # Only the on-record match feeds the canonical aggregation.
    assert prof.efficiency.n == 1
    assert set(prof.per_persona) == {"fair"}
    assert prof.excluded == 1
    assert prof.off_record is False


def test_off_record_does_not_change_canonical_score():
    sc, an = _hand()
    on = [
        score_match(sc, an, MatchResult(True, Offer((1, 0)), [], 2, 8), "fair"),
        score_match(sc, an, MatchResult(True, Offer((1, 0)), [], 2, 8), "tough"),
    ]
    off = score_match(
        sc, an, MatchResult(False, None, [], 16, 8), "slippery", off_record=True
    )
    clean = build_profile("x", on)
    polluted_attempt = build_profile("x", on + [off])
    # Adding an off-record (here, no-deal) match must not move the canonical mean/deal_rate.
    assert polluted_attempt.efficiency.mean == clean.efficiency.mean
    assert polluted_attempt.deal_rate == clean.deal_rate
    assert polluted_attempt.excluded == 1


def test_build_off_record_profile_is_flagged():
    sc, an = _hand()
    m = score_match(
        sc, an, MatchResult(True, Offer((1, 0)), [], 2, 8), "fair", off_record=True
    )
    prof = build_off_record_profile("x", [m])
    assert prof.off_record is True
    assert prof.efficiency.n == 1  # off-record profiles still aggregate their own matches


# --- run-log schema (D-029 additions) ---------------------------------------------------

def test_runlog_emits_schema_version_and_off_record(tmp_path):
    suite = Suite(seed=1, n_scenarios=2)
    profile, records = run_suite(suite, make_agent("heuristic"), Nudge(swap_persona="tough"))
    run_dir = write_run(profile, records, suite, out_root=str(tmp_path), off_record=True)
    payload = json.loads((run_dir / "run.json").read_text(encoding="utf-8"))

    assert payload["schema_version"] == SCHEMA_VERSION
    assert payload["off_record"] is True
    # Existing top-level fields remain present and in place.
    assert list(payload.keys())[-3:] == ["suite", "profile", "matches"]
    # Existing per-match fields remain present; off_record is appended last (D-029).
    # (n_issues/n_levels were added by D-032 when scenario shapes began to vary.)
    keys = list(payload["matches"][0].keys())
    assert {
        "scenario_seed", "persona", "agreed", "outcome", "efficiency",
        "own_value", "turns_used", "transcript", "analysis",
    }.issubset(keys)
    assert keys[-1] == "off_record"


def test_runlog_canonical_run_is_on_record(tmp_path):
    suite = Suite(seed=1, n_scenarios=2)
    profile, records = run_suite(suite, make_agent("heuristic"))
    run_dir = write_run(profile, records, suite, out_root=str(tmp_path))
    payload = json.loads((run_dir / "run.json").read_text(encoding="utf-8"))
    assert payload["off_record"] is False  # inferred from the on-record profile
