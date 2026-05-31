"""The fixed coding-ride suite + aggregation (decision D-039).

Scoring (D-019-style: objective payoff vs. an exact ceiling):

    task score = (# hidden tests passed) / (# hidden tests)   in [0, 1]

`optimal` play emits the reference for every task, so it scores 1.0 by construction. A `random`
floor stubs every task and scores ~0. A *score* over the ride is the **mean of the per-task scores**
across the fixed curated `TASK_SUITE`, reported with a 95% CI (reusing `scoring.Stat`, exactly as
the negotiation and economic rides do, so variance — the reproducibility evidence — is reported the
same way across rides).

Everything is seed-derived: the suite seed drives the hidden-test inputs (and any agent RNG), so the
same seed ⇒ identical tests ⇒ identical scores. Because inputs are *generated* (not fixed), a correct
implementation scores 1.0 for **any** seed while a memorize-the-answers agent cannot (D-039).
"""

from __future__ import annotations

from dataclasses import dataclass

from ..scoring import Stat
from .agents import CodingAgent
from .harness import DEFAULT_N_TESTS, TaskResult, grade
from .tasks import TASK_SUITE, CodingTask


@dataclass
class SuiteResult:
    agent_name: str
    score: Stat  # mean ± 95% CI of per-task pass rate
    compile_rate: float  # fraction of tasks whose emitted source compiled + exposed the entry point
    by_difficulty: dict[int, float]  # mean task score within each difficulty tier (1=easy..3=hard)
    tasks: list  # list[TaskResult] — the per-task breakdown


def _build_tasks() -> tuple[CodingTask, ...]:
    """The fixed suite of curated tasks (constant — the seed parameterizes the hidden tests)."""
    return TASK_SUITE


def run_suite(agent: CodingAgent, seed: int = 1, n_tests: int = DEFAULT_N_TESTS) -> SuiteResult:
    """Run a coding agent through the fixed task suite and aggregate its profile.

    Each task re-seeds the agent deterministically before asking it to `solve`, then the harness
    grades the emitted source on `n_tests` seeded hidden tests. The per-task scores roll up into a
    mean ± 95% CI plus a per-difficulty-tier breakdown.
    """
    tasks = _build_tasks()
    rows: list[TaskResult] = []
    for idx, task in enumerate(tasks):
        agent.reset(seed=seed * 1_000_003 + idx)
        source = agent.solve(task)
        rows.append(grade(task, source, seed=seed, n_tests=n_tests))

    compile_rate = (sum(1 for r in rows if r.compiled) / len(rows)) if rows else 0.0

    by_difficulty: dict[int, float] = {}
    for tier in sorted({r.difficulty for r in rows}):
        tier_rows = [r.score for r in rows if r.difficulty == tier]
        by_difficulty[tier] = sum(tier_rows) / len(tier_rows)

    return SuiteResult(
        agent_name=getattr(agent, "name", "agent"),
        score=Stat.of([r.score for r in rows]),
        compile_rate=compile_rate,
        by_difficulty=by_difficulty,
        tasks=rows,
    )
