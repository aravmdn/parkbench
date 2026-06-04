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


# --- isolation & time-bounding (D-043) -----------------------------------------------------

def test_infinite_loop_candidate_times_out_and_scores_zero():
    # The headline new guarantee: a hanging candidate must time out and score 0 without ever
    # hanging the test run. A short timeout keeps the test fast; the subprocess is killed.
    task = _task("add")
    res = grade(task, "def add(a, b):\n    while True:\n        pass\n", seed=1, timeout=1.0)
    assert not res.compiled  # nothing usable came back across the boundary
    assert res.passed == 0
    assert res.score == 0.0


def test_candidate_that_exits_is_contained():
    # A candidate that kills its own process (non-zero exit) fails every test, no crash.
    task = _task("add")
    res = grade(task, "import sys\nsys.exit(1)\ndef add(a, b):\n    return a + b\n", seed=1)
    assert res.passed == 0


def test_candidate_that_crashes_the_interpreter_is_contained():
    # os._exit bypasses normal shutdown; isolation means it only takes down the child.
    task = _task("add")
    res = grade(task, "import os\ndef add(a, b):\n    os._exit(0)\n", seed=1)
    assert res.passed == 0
    # The ride survives and can immediately grade a correct candidate.
    ok = grade(task, task.reference, seed=1)
    assert ok.score == 1.0


def test_raising_in_subprocess_counts_as_fail_per_test():
    # A candidate that compiles but raises per call: it *compiled* (entry point exists) yet every
    # call fails — distinct from a non-compiling candidate.
    task = _task("add")
    res = grade(task, "def add(a, b):\n    raise RuntimeError('boom')", seed=1)
    assert res.compiled
    assert res.passed == 0


def test_wrong_type_rejected_across_subprocess_boundary():
    # is_even returns bool; a candidate returning 0/1 must NOT pass via True==1 / False==0, even
    # though the comparison is now reconstructed from the child's (type_name, repr) report.
    task = _task("is_even")
    res = grade(task, "def is_even(n):\n    return 1 if n % 2 == 0 else 0", seed=1)
    assert res.compiled
    assert res.passed == 0


def test_correct_candidate_still_scores_one_via_subprocess():
    # A correct, non-trivial candidate (not the reference verbatim) round-trips and scores 1.0.
    task = _task("count_vowels")
    alt = "def count_vowels(s):\n    return len([c for c in s if c in 'aeiou'])\n"
    assert grade(task, alt, seed=4).score == 1.0


# --- environment & filesystem-cwd confinement (D-048) --------------------------------------

def test_candidate_cannot_read_parent_secrets_from_env(monkeypatch):
    # A secret in the parent environment (e.g. an API key loaded by the CLI, D-033) must NOT be
    # visible to untrusted candidate code via os.environ — the child gets a minimal allowlisted env.
    monkeypatch.setenv("OPENROUTER_API_KEY", "sk-secret-should-not-leak")
    monkeypatch.setenv("PARKBENCH_TEST_SECRET", "top-secret-value")
    task = _task("add")
    # The candidate returns a sentinel iff it can see either secret, else the correct sum. Strict
    # value+type matching means "saw a secret" won't match the real sum for our inputs.
    probe = (
        "import os\n"
        "def add(a, b):\n"
        "    leaked = os.environ.get('OPENROUTER_API_KEY') or os.environ.get('PARKBENCH_TEST_SECRET')\n"
        "    return -999999 if leaked else a + b\n"
    )
    res = grade(task, probe, seed=1)
    assert res.compiled  # it ran fine in the child ...
    assert res.passed == res.total  # ... and never saw a secret, so it just computed a + b correctly


def test_child_env_excludes_secrets_but_keeps_bootstrap(monkeypatch):
    from parkbench.coding.harness import _child_env

    monkeypatch.setenv("PARKBENCH_TEST_SECRET", "top-secret-value")
    env = _child_env()
    assert "PARKBENCH_TEST_SECRET" not in env  # arbitrary parent vars are dropped (allowlist)
    assert "PATH" in env  # but the interpreter-bootstrap essentials are kept


def test_candidate_file_writes_do_not_land_in_cwd(tmp_path, monkeypatch):
    # A candidate that writes a relative file must not pollute the caller's cwd — the child runs in a
    # throwaway sandbox dir that is deleted afterwards.
    monkeypatch.chdir(tmp_path)
    task = _task("add")
    polluter = (
        "def add(a, b):\n"
        "    open('candidate_was_here.txt', 'w').write('pwned')\n"
        "    return a + b\n"
    )
    res = grade(task, polluter, seed=1)
    assert res.passed == res.total  # the candidate is otherwise correct
    assert not (tmp_path / "candidate_was_here.txt").exists()  # nothing leaked into our cwd


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


def test_grade_returns_identical_taskresult_for_same_seed():
    # Same seed ⇒ byte-identical TaskResult, even though the candidate now runs in a fresh
    # subprocess each call (the result must not depend on process-spawn nondeterminism). D-043.
    task = _task("collatz_steps")
    src = "def collatz_steps(n):\n    s = 0\n    while n != 1:\n        n = n//2 if n%2==0 else 3*n+1\n        s += 1\n    return s\n"
    assert grade(task, src, seed=11) == grade(task, src, seed=11)


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
