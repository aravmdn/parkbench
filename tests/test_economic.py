"""Tests for the economic (knapsack) ride (decision D-036).

Covers: optimum correctness on a tiny hand-checkable instance (DP vs. brute force), full
determinism (same seed ⇒ identical), the score ordering optimal == 1.0 >= greedy/heuristic >
random in aggregate, and the `Ride` contract (registered as "economic", axis "economic",
score in [0, 1]).
"""

from __future__ import annotations

from parkbench.axis import RideResult
from parkbench.economic import (
    EconomicRide,
    generate_scenario,
    make_agent,
    optimal_value,
    run_suite,
    score_allocation,
)
from parkbench.economic.agents import AGENT_REGISTRY
from parkbench.economic.scenario import Item, KnapsackScenario, brute_optimum, solve_optimum
from parkbench.rides import RIDE_REGISTRY, Ride


# --- optimum correctness -------------------------------------------------------------------

def test_optimum_tiny_hand_checked():
    # Items (value, weight); budget 5.
    #   a=(60,5)  b=(50,3)  c=(40,2)
    # b+c: weight 5, value 90 -> best. a alone: value 60. So optimum = 90 taking {b, c}.
    sc = KnapsackScenario((Item(60, 5), Item(50, 3), Item(40, 2)), budget=5, seed=None)
    value, chosen = solve_optimum(sc)
    assert value == 90
    assert chosen == (1, 2)
    assert sc.is_feasible(chosen)


def test_dp_matches_brute_force_across_seeds():
    # The DP optimum must equal exhaustive enumeration on every generated instance.
    for seed in range(20):
        sc = generate_scenario(seed)
        assert optimal_value(sc) == brute_optimum(sc)


def test_greedy_can_be_suboptimal():
    # Classic knapsack gap: ratio-greedy takes the high-ratio small item and misses the optimum.
    #   a=(6,1, ratio 6)  b=(10,2, ratio 5)  c=(10,2, ratio 5); budget 4.
    # Greedy by ratio: a (w1) then b (w3) -> value 16, can't fit c. Optimum: b+c = 20.
    sc = KnapsackScenario((Item(6, 1), Item(10, 2), Item(10, 2)), budget=4, seed=None)
    assert optimal_value(sc) == 20
    greedy_choice = make_agent("greedy").choose(sc)
    assert sc.total_value(greedy_choice) < 20


# --- scoring -------------------------------------------------------------------------------

def test_score_is_ratio_and_clamps_infeasible():
    sc = KnapsackScenario((Item(60, 5), Item(50, 3), Item(40, 2)), budget=5, seed=None)
    assert score_allocation(sc, (1, 2)) == 1.0  # the optimum
    assert score_allocation(sc, (0,)) == 60 / 90  # achieved/optimal
    assert score_allocation(sc, ()) == 0.0  # empty allocation
    assert score_allocation(sc, (0, 1, 2)) == 0.0  # over budget -> infeasible -> 0
    assert score_allocation(sc, (5,)) == 0.0  # out-of-range index -> infeasible -> 0
    assert score_allocation(sc, (1, 1)) == 0.0  # duplicate index -> infeasible -> 0


def test_optimal_agent_scores_exactly_one():
    res = run_suite(make_agent("optimal"), seed=1)
    assert res.score.mean == 1.0
    assert all(r.score == 1.0 for r in res.scenarios)


# --- determinism ---------------------------------------------------------------------------

def test_generate_scenario_is_deterministic():
    a = generate_scenario(7)
    b = generate_scenario(7)
    assert a == b
    assert generate_scenario(7) != generate_scenario(8)


def test_suite_is_deterministic():
    for name in AGENT_REGISTRY:
        r1 = run_suite(make_agent(name), seed=3)
        r2 = run_suite(make_agent(name), seed=3)
        assert r1.score.mean == r2.score.mean
        assert [s.score for s in r1.scenarios] == [s.score for s in r2.scenarios]


def test_ride_evaluate_is_deterministic():
    ride = EconomicRide()
    assert ride.evaluate("greedy", seed=1).score == ride.evaluate("greedy", seed=1).score


# --- score ordering (in aggregate) ---------------------------------------------------------

def test_score_ordering():
    optimal = run_suite(make_agent("optimal"), seed=1).score.mean
    greedy = run_suite(make_agent("greedy"), seed=1).score.mean
    heuristic = run_suite(make_agent("heuristic"), seed=1).score.mean
    random_floor = run_suite(make_agent("random"), seed=1).score.mean

    assert optimal == 1.0
    assert optimal >= greedy > random_floor
    assert optimal >= heuristic > random_floor
    assert heuristic >= greedy  # the local-improvement pass never hurts


# --- the Ride contract (D-035) -------------------------------------------------------------

def test_economic_registered_and_conforms():
    ride = RIDE_REGISTRY["economic"]
    assert isinstance(ride, Ride)  # runtime_checkable Protocol
    assert ride.name == "economic"
    assert ride.axis == "economic"


def test_registry_evaluate_returns_rideresult():
    r = RIDE_REGISTRY["economic"].evaluate("greedy", seed=1)
    assert isinstance(r, RideResult)
    assert r.axis == "economic"
    assert r.agent == "greedy"
    assert 0.0 <= r.score <= 1.0
    assert r.detail["n_scenarios"] == 12


def test_all_baselines_run_through_registry():
    for name in ("random", "greedy", "heuristic", "optimal"):
        r = RIDE_REGISTRY["economic"].evaluate(name, seed=1)
        assert 0.0 <= r.score <= 1.0
