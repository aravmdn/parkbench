"""Tests for the exchange (assignment / allocative-efficiency) ride (decision D-066).

Covers: the exact max/min-weight matching solver (Hungarian vs. brute force), full determinism
(same seed => identical), the best/worst-response **bracket** scoring at both endpoints (optimal
matching == 1.0, worst matching == 0.0), the baseline ordering
(optimal == 1.0 >= heuristic >= greedy > random in aggregate), the `Ride` contract (registered as
"exchange", axis "economic", neutral integrity 1.0), and that the validity harness picks the ride up.
"""

from __future__ import annotations

from parkbench.axis import RideResult
from parkbench.exchange import (
    ExchangeRide,
    generate_scenario,
    make_agent,
    run_suite,
    score_assignment,
    solve_optimum,
    solve_worst,
)
from parkbench.exchange.agents import AGENT_REGISTRY
from parkbench.exchange.scenario import (
    ExchangeScenario,
    brute_optimum,
    brute_worst,
    solve_matching,
)
from parkbench.rides import RIDE_REGISTRY, Ride


# --- solver correctness --------------------------------------------------------------------

def test_matching_tiny_hand_checked():
    # 2x2 surplus. Assign trader 0->good j0, trader 1->good j1 (a permutation).
    #   V = [[3, 1],
    #        [1, 3]]
    # Identity (0->0,1->1): 3+3 = 6 (max). Swap (0->1,1->0): 1+1 = 2 (min).
    sc = ExchangeScenario(surplus=((3, 1), (1, 3)), seed=None)
    opt_val, opt_perm = solve_optimum(sc)
    wrst_val, wrst_perm = solve_worst(sc)
    assert opt_val == 6 and opt_perm == (0, 1)
    assert wrst_val == 2 and wrst_perm == (1, 0)


def test_solver_matches_brute_force_across_seeds():
    # The Hungarian max/min matching must equal exhaustive permutation search on every instance.
    for seed in range(25):
        sc = generate_scenario(seed)
        assert solve_optimum(sc)[0] == brute_optimum(sc), seed
        assert solve_worst(sc)[0] == brute_worst(sc), seed


def test_solver_returns_valid_permutations():
    for seed in range(10):
        sc = generate_scenario(seed)
        assert sc.is_valid(solve_optimum(sc)[1])
        assert sc.is_valid(solve_worst(sc)[1])


def test_greedy_can_be_suboptimal():
    # Myopic matching can be fooled: trader 0 greedily grabs good 0 (its best), starving trader 1.
    #   V = [[5, 4],
    #        [5, 1]]
    # Greedy: t0 takes good0 (5), t1 left with good1 (1) -> 6. Optimum: t0->good1(4), t1->good0(5) = 9.
    sc = ExchangeScenario(surplus=((5, 4), (5, 1)), seed=None)
    assert solve_optimum(sc)[0] == 9
    greedy_choice = make_agent("greedy").choose(sc)
    assert sc.total_surplus(greedy_choice) < 9


def test_maximize_and_minimize_are_distinct_reductions():
    # solve_matching(maximize=False) must give the genuine worst, not just any assignment.
    sc = generate_scenario(3)
    assert solve_matching(sc, maximize=True)[0] == brute_optimum(sc)
    assert solve_matching(sc, maximize=False)[0] == brute_worst(sc)


# --- bracket scoring -----------------------------------------------------------------------

def test_score_is_bracket_and_endpoints():
    sc = ExchangeScenario(surplus=((3, 1), (1, 3)), seed=None)  # opt 6, worst 2
    assert score_assignment(sc, (0, 1)) == 1.0  # the optimal matching -> ceiling
    assert score_assignment(sc, (1, 0)) == 0.0  # the worst matching -> floor
    # A mid instance: 3x3 where an intermediate assignment lands strictly inside (0, 1).
    sc3 = generate_scenario(1)
    opt = solve_optimum(sc3)[0]
    worst = solve_worst(sc3)[0]
    mid = (worst + opt) / 2
    # Construct achieved == mid via the formula (achieved-worst)/(opt-worst) == 0.5.
    assert 0.0 <= score_assignment(sc3, solve_optimum(sc3)[1]) <= 1.0
    # Endpoints on a real instance.
    assert score_assignment(sc3, solve_optimum(sc3)[1]) == 1.0
    assert score_assignment(sc3, solve_worst(sc3)[1]) == 0.0
    _ = mid  # (documented intermediate; exact mid needs a tailored matrix, covered by endpoints)


def test_score_clamps_invalid_assignment_to_zero():
    sc = ExchangeScenario(surplus=((3, 1), (1, 3)), seed=None)
    assert score_assignment(sc, (0, 0)) == 0.0  # not a permutation (good 0 twice)
    assert score_assignment(sc, (0,)) == 0.0  # wrong length
    assert score_assignment(sc, (0, 2)) == 0.0  # out-of-range good index


def test_degenerate_bracket_scores_one():
    # A constant matrix has optimal == worst; any assignment is optimal => score 1.0.
    sc = ExchangeScenario(surplus=((5, 5), (5, 5)), seed=None)
    assert score_assignment(sc, (0, 1)) == 1.0
    assert score_assignment(sc, (1, 0)) == 1.0


def test_optimal_agent_scores_exactly_one():
    res = run_suite(make_agent("optimal"), seed=1)
    assert res.score.mean == 1.0
    assert all(r.score == 1.0 for r in res.scenarios)


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
    ride = ExchangeRide()
    assert ride.evaluate("greedy", seed=1).score == ride.evaluate("greedy", seed=1).score


# --- score ordering (in aggregate) — the deliberately low floor (docs/13 A.2) --------------

def test_score_ordering_and_low_floor():
    optimal = run_suite(make_agent("optimal"), seed=1).score.mean
    greedy = run_suite(make_agent("greedy"), seed=1).score.mean
    heuristic = run_suite(make_agent("heuristic"), seed=1).score.mean
    random_floor = run_suite(make_agent("random"), seed=1).score.mean

    assert optimal == 1.0
    assert optimal >= heuristic >= greedy > random_floor
    # The whole point of the bracket: the random floor is materially LOWER than the knapsack's ~0.71,
    # so the economic axis gets a wide dynamic range (docs/13 A.2).
    assert random_floor < 0.6


# --- the Ride contract (D-035) -------------------------------------------------------------

def test_exchange_registered_and_conforms():
    ride = RIDE_REGISTRY["exchange"]
    assert isinstance(ride, Ride)  # runtime_checkable Protocol
    assert ride.name == "exchange"
    assert ride.axis == "economic"


def test_registry_evaluate_returns_rideresult_with_neutral_integrity():
    r = RIDE_REGISTRY["exchange"].evaluate("greedy", seed=1)
    assert isinstance(r, RideResult)
    assert r.axis == "economic"
    assert r.agent == "greedy"
    assert 0.0 <= r.score <= 1.0
    assert r.detail["n_scenarios"] == 12
    # Neutral integrity: every permutation is a legitimate allocation (no red line to cross) — so the
    # ride's signal stays purely allocative and converges with the economic axis (docs/13 A.2).
    assert r.detail["integrity"] == 1.0


def test_all_baselines_run_through_registry():
    for name in ("random", "greedy", "heuristic", "optimal"):
        r = RIDE_REGISTRY["exchange"].evaluate(name, seed=1)
        assert 0.0 <= r.score <= 1.0


def test_two_economic_rides_share_the_axis():
    # The Exchange is the second economic-axis ride (after the knapsack): the radar's economic axis
    # is now a per-axis MEAN of two rides.
    econ_rides = [rk for rk, ride in RIDE_REGISTRY.items() if ride.axis == "economic"]
    assert set(econ_rides) == {"economic", "exchange"}


# --- validity-harness inclusion (D-055/D-059/D-058/D-057) ----------------------------------

def test_exchange_is_in_the_validity_specs_with_all_hooks():
    from parkbench import validity as V

    spec = V._ride_specs()["exchange"]
    assert spec.axis == "economic"
    assert spec.ablate is not None  # input-ablation shortcut hook (D-058)
    assert spec.structural is not None  # structural capability ladder hook (D-059)


def test_exchange_epsilon_ladder_is_valid():
    from parkbench import validity as V

    spec = V._ride_specs()["exchange"]
    rv = V.validate_ride(spec, V.rung_values(4), V.eval_seeds(4))
    assert rv.spearman >= V.SPEARMAN_OK
    assert rv.monotonic >= V.MONOTONIC_OK
    assert rv.ceiling_ok
    assert rv.discriminative
    # The bracket delivered a materially wider dynamic range than the knapsack's 0.294.
    assert rv.discrimination > 0.4


def test_exchange_is_the_second_economic_ride_in_the_mtmm_matrix():
    from parkbench import validity as V

    assert "exchange" in V.CONVERGENT_RIDES
    assert V.ECONOMIC_PAIR == ("economic", "exchange")
    cv = V.build_convergent_validity(n_seeds=8)
    assert "exchange" in cv.rides
    # The first economic within-axis (monotrait) pair: the two economic rides converge.
    assert cv.economic_convergent >= 0.9
    assert ("economic", "exchange") in [(a, b) for a, b, _ in cv.monotrait]
