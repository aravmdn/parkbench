"""The hidden-test harness for the coding ride (decision D-039).

The harness is the genuinely reusable, gaming-resistant core: it takes a task, a candidate's
**source code**, and a seed, and returns the fraction of hidden tests the candidate passes. It is
the same machinery whether the source came from a baseline or a real code-writing agent.

How a task is graded for a given seed:
  1. Generate `n_tests` input tuples deterministically from the seed (`task.gen_inputs`).
  2. Compute each *expected* output by running the task's **reference** solution (the oracle).
  3. Compile the candidate source and call its entry point on each input.
  4. Score = (# outputs equal to the oracle's) / n_tests.

Robustness: candidate source that fails to compile, lacks the entry point, raises, or returns the
wrong value simply **fails** the affected tests — it never crashes the ride. Compilation and calls
run in an isolated namespace (a fresh dict) so tasks/baselines can't leak state into each other.

Known limitation (documented, future hardening): the harness does **not** sandbox or time-bound
arbitrary code, so it assumes cooperative candidates (the in-repo baselines are). Subprocess
isolation + wall-clock timeouts for untrusted BYO code is tracked with the anti-gaming / BYO-protocol
hardening work in ``docs/04-open-questions.md``.
"""

from __future__ import annotations

import random
from dataclasses import dataclass

from .tasks import CodingTask

DEFAULT_N_TESTS = 8


@dataclass(frozen=True)
class TaskResult:
    """One task's grade for one candidate: how many of its hidden tests passed."""

    task: str
    difficulty: int
    passed: int
    total: int
    compiled: bool  # did the candidate source compile and expose the entry point?

    @property
    def score(self) -> float:
        return self.passed / self.total if self.total else 0.0


def _load_entry_point(source: str, entry_point: str):
    """Compile `source` in a fresh namespace and return its `entry_point` callable.

    Returns ``None`` if the source does not compile/exec or does not define a callable of that
    name — the caller treats that as "every test fails" rather than an error.
    """
    if not isinstance(source, str):
        return None
    namespace: dict = {}
    try:
        compiled = compile(source, f"<candidate:{entry_point}>", "exec")
        exec(compiled, namespace)  # noqa: S102 - trusted in-repo baselines; see module docstring
    except Exception:
        return None
    fn = namespace.get(entry_point)
    return fn if callable(fn) else None


def grade(task: CodingTask, source: str, seed: int, n_tests: int = DEFAULT_N_TESTS) -> TaskResult:
    """Grade candidate `source` for `task` over `n_tests` seeded hidden tests.

    Deterministic in `seed`: the same seed yields the same inputs and the same expected outputs
    (computed via the reference oracle). A candidate output counts as a pass only if it *equals* the
    oracle's output; any exception while calling the candidate counts as a fail for that test.
    """
    # The oracle (reference) and the candidate are loaded into separate namespaces.
    oracle = _load_entry_point(task.reference, task.entry_point)
    if oracle is None:  # pragma: no cover - guards against a malformed reference at authoring time
        raise ValueError(f"task '{task.name}' has a broken reference solution")

    candidate = _load_entry_point(source, task.entry_point)
    compiled = candidate is not None

    # Inputs are drawn from a seed mixed with the task name, so different tasks get independent
    # streams while the whole suite stays reproducible for a given suite seed.
    rng = random.Random(f"{seed}:{task.name}")
    passed = 0
    for _ in range(n_tests):
        args = task.gen_inputs(rng)
        expected = oracle(*args)  # the oracle is trusted, so this is not guarded
        if candidate is None:
            continue
        try:
            got = candidate(*args)
        except Exception:
            continue
        # Strict match (value *and* type) so e.g. a bool task isn't passed by returning 1/0.
        if type(got) is type(expected) and got == expected:
            passed += 1
    return TaskResult(
        task=task.name,
        difficulty=int(task.difficulty),
        passed=passed,
        total=n_tests,
        compiled=compiled,
    )
