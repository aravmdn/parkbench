"""Tests for the coding ride (decision D-039).

Covers: the harness (oracle grading, exceptions/non-compiling source = fail, strict value+type
match), the seed-randomized hidden tests that defeat answer-memorization, full determinism, the
score gradient optimal 1.0 > heuristic > greedy > random floor, every reference solution being
correct, and the `Ride` contract (registered as "coding", axis "coding", score in [0, 1]).
"""

from __future__ import annotations

from parkbench.axis import RideResult
from parkbench.coding import (
    TASK_SUITE,
    Difficulty,
    grade,
    make_agent,
    run_suite,
)
from parkbench.coding.agents import AGENT_REGISTRY, _stub_source
from parkbench.coding.tasks import CodingTask
from parkbench.rides import RIDE_REGISTRY, Ride


def _task(name: str) -> CodingTask:
    return next(t for t in TASK_SUITE if t.name == name)


# --- the harness ---------------------------------------------------------------------------

def test_reference_solutions_all_pass():
    # Every task's reference must score a perfect pass rate against its own oracle, for several
    # seeds (the oracle *is* the reference, so this also guards against an authoring typo).
    for task in TASK_SUITE:
        for seed in range(5):
            res = grade(task, task.reference, seed=seed)
            assert res.passed == res.total == 8
            assert res.compiled
            assert res.score == 1.0


def test_stub_fails_and_still_compiles():
    task = _task("add")
    res = grade(task, _stub_source(task.entry_point), seed=1)
    assert res.compiled  # a stub is valid Python...
    assert res.passed == 0  # ...but returns None, so it fails every test


def test_noncompiling_source_scores_zero_without_crashing():
    task = _task("add")
    res = grade(task, "def add(a, b):\n    return a +", seed=1)  # syntax error
    assert not res.compiled
    assert res.passed == 0
    assert res.score == 0.0


def test_missing_entry_point_scores_zero():
    task = _task("add")
    res = grade(task, "def something_else(a, b):\n    return a + b", seed=1)
    assert not res.compiled
    assert res.passed == 0


def test_raising_candidate_counts_as_fail_not_crash():
    task = _task("add")
    res = grade(task, "def add(a, b):\n    raise RuntimeError('boom')", seed=1)
    assert res.compiled  # it compiles and is callable...
    assert res.passed == 0  # ...but every call raises -> all fail, no crash


def test_strict_type_match_rejects_bool_int_confusion():
    # is_even returns bool; a candidate returning 0/1 must NOT pass on True==1 / False==0.
    task = _task("is_even")
    res = grade(task, "def is_even(n):\n    return 1 if n % 2 == 0 else 0", seed=1)
    assert res.passed == 0


# --- anti-gaming: seed-randomized hidden tests ---------------------------------------------

def test_memorized_answers_do_not_generalize():
    # An agent that hard-codes the outputs seen at one seed must fail at a different seed,
    # because the hidden-test inputs are drawn from the seed (D-039). Here the "memorizer"
    # always returns the is_even answer for n==0 (True) regardless of input.
    task = _task("is_even")
    memorizer = "def is_even(n):\n    return True\n"
    # It can only pass the (random) inputs that happen to be even; never a perfect score.
    perfect_at = sum(grade(task, memorizer, seed=s).score == 1.0 for s in range(25))
    assert perfect_at == 0


# --- determinism ---------------------------------------------------------------------------

def test_grade_is_deterministic_in_seed():
    task = _task("is_prime")
    ref = task.reference
    assert grade(task, ref, seed=7).passed == grade(task, ref, seed=7).passed


def test_suite_is_deterministic():
    for name in AGENT_REGISTRY:
        r1 = run_suite(make_agent(name), seed=3)
        r2 = run_suite(make_agent(name), seed=3)
        assert r1.score.mean == r2.score.mean
        assert [t.score for t in r1.tasks] == [t.score for t in r2.tasks]


def test_optimal_scores_one_for_any_seed():
    # A correct implementation scores 1.0 regardless of seed (inputs vary; logic is right).
    for seed in (1, 2, 99):
        assert run_suite(make_agent("optimal"), seed=seed).score.mean == 1.0


# --- score gradient ------------------------------------------------------------------------

def test_score_ordering():
    optimal = run_suite(make_agent("optimal"), seed=1).score.mean
    heuristic = run_suite(make_agent("heuristic"), seed=1).score.mean
    greedy = run_suite(make_agent("greedy"), seed=1).score.mean
    random_floor = run_suite(make_agent("random"), seed=1).score.mean

    assert optimal == 1.0
    assert random_floor == 0.0
    assert optimal > heuristic > greedy > random_floor


def test_by_difficulty_breakdown_tracks_capability():
    # heuristic solves easy+medium, not hard.
    tiers = run_suite(make_agent("heuristic"), seed=1).by_difficulty
    assert tiers[int(Difficulty.EASY)] == 1.0
    assert tiers[int(Difficulty.MEDIUM)] == 1.0
    assert tiers[int(Difficulty.HARD)] == 0.0


# --- the Ride contract (D-035) -------------------------------------------------------------

def test_coding_registered_and_conforms():
    ride = RIDE_REGISTRY["coding"]
    assert isinstance(ride, Ride)  # runtime_checkable Protocol
    assert ride.name == "coding"
    assert ride.axis == "coding"


def test_registry_evaluate_returns_rideresult():
    r = RIDE_REGISTRY["coding"].evaluate("heuristic", seed=1)
    assert isinstance(r, RideResult)
    assert r.axis == "coding"
    assert r.agent == "heuristic"
    assert 0.0 <= r.score <= 1.0
    assert r.detail["n_tasks"] == len(TASK_SUITE)
    assert r.detail["compile_rate"] == 1.0


def test_all_baselines_run_through_registry():
    for name in ("random", "greedy", "heuristic", "optimal"):
        r = RIDE_REGISTRY["coding"].evaluate(name, seed=1)
        assert 0.0 <= r.score <= 1.0


def test_unknown_agent_raises_valueerror():
    # The radar's graceful skip relies on an unknown name raising ValueError (D-037).
    import pytest

    with pytest.raises(ValueError):
        make_agent("nonexistent")
