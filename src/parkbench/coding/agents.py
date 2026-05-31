"""Baseline agents for the coding ride (decision D-039).

Each ride owns its own agent interface (D-035). A `CodingAgent` is anything that, given a
`CodingTask`, returns **source code** (a string) defining the task's entry-point function. The
harness (`coding/harness.py`) then grades that source against seeded hidden tests — identically for
a baseline or a real code-writing agent.

The four baselines reuse the **same names** as the other rides (`random` / `greedy` / `heuristic` /
`optimal`) so the radar roll-up (D-037) can profile one shared agent name across all axes. They
model **capability tiers**: an agent reliably solves tasks up to a difficulty ceiling and stubs the
rest. This calibrates the ``[0, 1]`` scale with a clean monotone gradient
(optimal > heuristic > greedy > random) — exactly the role `optimal` (the DP ceiling) and `random`
(the floor) play in the economic ride.

  - `random`    — floor: emits a stub that returns ``None`` for every task (fails ~all tests).
  - `greedy`    — solves EASY tasks; stubs MEDIUM/HARD.
  - `heuristic` — solves EASY + MEDIUM tasks; stubs HARD.
  - `optimal`   — solves everything (emits each task's reference); the score ceiling (1.0).
"""

from __future__ import annotations

import abc
import random

from .tasks import CodingTask, Difficulty


def _stub_source(entry_point: str) -> str:
    """A syntactically valid but wrong solution: defines the entry point, always returns None."""
    return f"def {entry_point}(*args, **kwargs):\n    return None\n"


class CodingAgent(abc.ABC):
    """Given a coding task, return source code defining `task.entry_point`.

    `name` is the agent's registry key (shared across rides for the radar roll-up). `reset(seed)`
    re-seeds any RNG so a whole suite reproduces exactly; stateless agents may ignore it.
    """

    name: str = "coding-agent"

    def reset(self, seed: int = 0) -> None:
        self.rng = random.Random(seed)

    @abc.abstractmethod
    def solve(self, task: CodingTask) -> str:
        """Return candidate source code for the task's entry-point function."""


class _TieredAgent(CodingAgent):
    """Solves tasks at or below `max_difficulty` (emitting the reference); stubs the rest."""

    max_difficulty: Difficulty

    def solve(self, task: CodingTask) -> str:
        if task.difficulty <= self.max_difficulty:
            return task.reference
        return _stub_source(task.entry_point)


class RandomAgent(CodingAgent):
    """Floor: emits a stub for every task (returns None — fails virtually every hidden test)."""

    name = "random"

    def solve(self, task: CodingTask) -> str:
        return _stub_source(task.entry_point)


class GreedyAgent(_TieredAgent):
    """Solves only the EASY tier."""

    name = "greedy"
    max_difficulty = Difficulty.EASY


class HeuristicAgent(_TieredAgent):
    """Solves the EASY + MEDIUM tiers."""

    name = "heuristic"
    max_difficulty = Difficulty.MEDIUM


class OptimalAgent(_TieredAgent):
    """Solves every tier — the score ceiling (always 1.0)."""

    name = "optimal"
    max_difficulty = Difficulty.HARD


AGENT_REGISTRY: dict[str, type[CodingAgent]] = {
    "random": RandomAgent,
    "greedy": GreedyAgent,
    "heuristic": HeuristicAgent,
    "optimal": OptimalAgent,
}


def make_agent(name: str) -> CodingAgent:
    try:
        return AGENT_REGISTRY[name]()
    except KeyError:
        raise ValueError(
            f"Unknown coding agent '{name}'. Choices: {', '.join(sorted(AGENT_REGISTRY))}"
        ) from None
