"""The agent interface every participant implements (house or bring-your-own)."""

from __future__ import annotations

import abc
import random

from ..protocol import Action, Observation


class Agent(abc.ABC):
    name: str = "agent"

    def reset(self, seed: int = 0, total_rounds: int = 8) -> None:
        """Called once before each match: re-seed the RNG and clear per-match state.

        Re-seeding here is what makes whole suites reproducible (the v1 claim).
        """
        self.rng = random.Random(seed)
        self.total_rounds = total_rounds

    @abc.abstractmethod
    def act(self, obs: Observation) -> Action:
        """Return this agent's move for the given observation."""
