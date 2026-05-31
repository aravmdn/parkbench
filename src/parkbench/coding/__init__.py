"""The coding ride: a solo code-generation test, hidden-test scored (decision D-039).

This is the project's **third** scored ride and the first on the **coding** axis (D-005), added so
the diagnostic radar (D-007/D-037) spans three axes. It is a clean *solo* ride (D-006): an agent is
handed a small, self-contained programming task and must emit **source code** for the task's entry
point; a hidden test harness runs that code and grades it on an objective pass rate, normalized to
``[0, 1]`` exactly like every other ride (D-035). Hidden-test inputs are seed-randomized so an agent
must implement real logic rather than memorize answers (D-039).

Public surface:
  - `CodingTask`, `TASK_SUITE`, `Difficulty` — the curated task suite + reference oracles
  - `grade`, `TaskResult` — the hidden-test harness
  - `CodingAgent` and the baselines `random`/`greedy`/`heuristic`/`optimal` (`make_agent`)
  - `run_suite` + `SuiteResult` — the fixed task suite with mean ± 95% CI
  - `CodingRide` — the `parkbench.rides.Ride` implementation (registered as `"coding"`)
"""

from __future__ import annotations

from .agents import AGENT_REGISTRY, CodingAgent, make_agent
from .harness import TaskResult, grade
from .ride import CodingRide
from .suite import SuiteResult, run_suite
from .tasks import TASK_SUITE, CodingTask, Difficulty

__all__ = [
    "CodingTask",
    "TASK_SUITE",
    "Difficulty",
    "grade",
    "TaskResult",
    "CodingAgent",
    "AGENT_REGISTRY",
    "make_agent",
    "SuiteResult",
    "run_suite",
    "CodingRide",
]
