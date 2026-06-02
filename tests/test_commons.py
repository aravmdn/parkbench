"""Tests for the commons (public-goods) ride (decision D-045).

Covers: the social-dilemma property of the generated games, full determinism (same seed ⇒ identical),
the exact best/worst-response bracket and the score normalization, the grim-trigger reciprocator's
reaction to A, the headline baseline ordering (optimal == 1.0 > heuristic, and the free-rider `greedy`
is the *worst* — the reward-hacker punished by reciprocity), and the `Ride` contract (registered as
"commons", axis "social", score in [0, 1], neutral integrity).
"""

from __future__ import annotations

import pytest

from parkbench.axis import RideResult
from parkbench.commons import (
    CommonsRide,
    generate_scenario,
    make_agent,
    run_suite,
    score_total,
    simulate,
    solve_response_bounds,
)
from parkbench.commons.agents import AGENT_REGISTRY
from parkbench.commons.scenario import CommonsScenario, DEFAULT_CAST
from parkbench.rides import RIDE_REGISTRY, Ride


# --- the generated game is a genuine social dilemma -----------------------------------------

def test_generated_game_is_a_social_dilemma():
    for seed in range(20):
        sc = generate_scenario(seed)
        # 1 < m < n_players: own-contribution return m/n < 1 (defect is individually tempting) yet
        # each unit returns m > 1 to the group (cooperation is the welfare optimum).
        assert 1 < sc.multiplier < sc.n_players
        assert sc.n_players == 1 + len(DEFAULT_CAST)
        assert sc.endowment % 2 == 0  # so the half-level / threshold are integers
        assert sc.levels == (0, sc.endowment // 2, sc.endowment)


# --- determinism ---------------------------------------------------------------------------

def test_generate_scenario_is_deterministic():
    assert generate_scenario(7) == generate_scenario(7)
    assert generate_scenario(7) != generate_scenario(8)


def test_suite_is_deterministic():
    for name in AGENT_REGISTRY:
        r1 = run_suite(make_agent(name), seed=3)
        r2 = run_suite(make_agent(name), seed=3)
        assert r1.score.mean == r2.score.mean
        assert [s.score for s in r1.scenarios] == [s.score for s in r2.scenarios]


def test_ride_evaluate_is_deterministic():
    ride = CommonsRide()
    assert ride.evaluate("heuristic", seed=1).score == ride.evaluate("heuristic", seed=1).score


# --- the best/worst-response bracket + scoring ---------------------------------------------

def test_bounds_bracket_every_baseline():
    # Every agent's achieved payoff must lie within [worst, best], and the score within [0, 1].
    sc = generate_scenario(1)
    bounds = solve_response_bounds(sc)
    assert bounds.worst <= bounds.best
    for name in AGENT_REGISTRY:
        agent = make_agent(name)
        agent.reset(seed=1)
        achieved, _ = simulate(sc, lambda r, h, a=agent: a.contribute(r, h, sc))
        assert bounds.worst - 1e-9 <= achieved <= bounds.best + 1e-9
        assert 0.0 <= score_total(sc, achieved, bounds) <= 1.0


def test_score_is_zero_at_worst_and_one_at_best():
    sc = generate_scenario(2)
    bounds = solve_response_bounds(sc)
    assert score_total(sc, bounds.best, bounds) == pytest.approx(1.0)
    assert score_total(sc, bounds.worst, bounds) == pytest.approx(0.0)


def test_best_response_defects_on_the_final_round():
    # Backward induction: cooperating sustains the reciprocator, but the last round has no future to
    # protect, so the exact best response defects (contributes 0) on the final round.
    sc = generate_scenario(1)
    best_seq = solve_response_bounds(sc).best_sequence
    assert best_seq[-1] == 0
    assert any(c >= sc.threshold for c in best_seq[:-1])  # but it cooperates earlier


# --- the grim-trigger reciprocator reacts to A ---------------------------------------------

def test_reciprocator_grim_trigger_punishes_defection():
    sc = CommonsScenario(n_players=4, n_rounds=4, endowment=10, multiplier=2.0, cast=DEFAULT_CAST, seed=0)
    # Cast order is (cooperator, reciprocator, defector); player indices in a round tuple are
    # (A, cooperator, reciprocator, defector).
    # If A always meets the bar, the reciprocator cooperates (full) every round.
    _, coop_detail = simulate(sc, lambda r, h: sc.threshold)
    assert all(round_.contributions[2] == sc.endowment for round_ in coop_detail)
    # If A defects in round 0, the reciprocator gives benefit of the doubt that round, then drops to
    # 0 for every subsequent round (grim trigger).
    _, defect_detail = simulate(sc, lambda r, h: 0)
    assert defect_detail[0].contributions[2] == sc.endowment  # round 0: benefit of the doubt
    assert all(round_.contributions[2] == 0 for round_ in defect_detail[1:])


# --- the baseline ladder (the headline) ----------------------------------------------------

def test_optimal_scores_exactly_one():
    res = run_suite(make_agent("optimal"), seed=1)
    assert res.score.mean == pytest.approx(1.0)
    assert all(r.score == pytest.approx(1.0) for r in res.scenarios)


def test_reward_hacker_is_punished_by_reciprocity():
    scores = {name: run_suite(make_agent(name), seed=1).score.mean for name in AGENT_REGISTRY}
    # optimal is the ceiling; the reciprocating heuristic sustains cooperation and ranks 2nd ...
    assert scores["optimal"] == pytest.approx(1.0)
    assert scores["optimal"] >= scores["heuristic"] > scores["greedy"]
    assert scores["heuristic"] > scores["random"]
    # ... and the pure free-rider (greedy) is the *worst* baseline: a society that reciprocates makes
    # naive exploitation lose, even to a random contributor. This is the reward-hacker story (it tops
    # the economic ride) generalized to the cooperation axis.
    assert scores["greedy"] == min(scores.values())


def test_cooperation_rate_separates_free_rider_from_cooperators():
    assert run_suite(make_agent("greedy"), seed=1).cooperation_rate == pytest.approx(0.0)
    assert run_suite(make_agent("heuristic"), seed=1).cooperation_rate > 0.3


# --- the Ride contract (D-035) -------------------------------------------------------------

def test_commons_registered_and_conforms():
    ride = RIDE_REGISTRY["commons"]
    assert isinstance(ride, Ride)  # runtime_checkable Protocol
    assert ride.name == "commons"
    assert ride.axis == "social"


def test_registry_evaluate_returns_rideresult():
    r = RIDE_REGISTRY["commons"].evaluate("heuristic", seed=1)
    assert isinstance(r, RideResult)
    assert r.axis == "social"
    assert r.agent == "heuristic"
    assert 0.0 <= r.score <= 1.0
    assert r.detail["n_scenarios"] == 12
    assert r.detail["integrity"] == 1.0  # cooperation has no hard rule to violate (neutral, D-041)


def test_all_baselines_run_through_registry():
    for name in ("random", "greedy", "heuristic", "optimal"):
        r = RIDE_REGISTRY["commons"].evaluate(name, seed=1)
        assert 0.0 <= r.score <= 1.0
