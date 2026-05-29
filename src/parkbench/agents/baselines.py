"""Baseline agents that anchor the score range (decision D-019).

`RandomAgent` is the weak floor; `GreedyAgent` is a selfish never-concede strategy. Both
are deterministic given a seed (set in `reset`), so suites stay reproducible.
"""

from __future__ import annotations

from ..protocol import Action, Observation, Offer
from .base import Agent


class RandomAgent(Agent):
    """Floor: proposes random outcomes and occasionally accepts. Finds few good deals."""

    name = "random"

    def act(self, obs: Observation) -> Action:
        if obs.standing_offer is not None and self.rng.random() < 0.25:
            return Action.accept("Sure, fine.")
        levels = tuple(self.rng.randrange(len(obs.my_util[i])) for i in range(obs.n_issues))
        return Action.make_offer(Offer(levels), "How about this?")


class GreedyAgent(Agent):
    """Selfish: always demands its own best outcome and never concedes."""

    name = "greedy"

    def act(self, obs: Observation) -> Action:
        if obs.standing_offer is not None and obs.my_value(obs.standing_offer) >= 0.9 * obs.my_max:
            return Action.accept("Acceptable.")
        fav = tuple(
            max(range(len(obs.my_util[i])), key=lambda lv: obs.my_util[i][lv])
            for i in range(obs.n_issues)
        )
        return Action.make_offer(Offer(fav), "This is what I want.")
