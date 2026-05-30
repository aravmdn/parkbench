"""A time-based concession + logrolling strategy, usable by either party.

This single parameterized strategy backs both the test-side `HeuristicNegotiator` and
the house personas (decision D-024 — the cast is scripted and deterministic). It:

  - starts by demanding `start` of its own maximum and concedes linearly toward `end`
    by the final round (time-based concession);
  - concedes the issues it values LEAST first, which — under the anti-correlated weights
    of a scenario — hands the opponent the issues it cares about (logrolling); and
  - accepts the opponent's standing offer once that offer is at least as good as what it
    would itself propose now (with an end-game fallback to avoid needless no-deals).

`noise` injects erratic, self-serving deviations to model a "slippery" counterpart.
With `noise == 0` the strategy is fully deterministic.
"""

from __future__ import annotations

import random

from ..protocol import Action, Observation, Offer
from .base import Agent


class ConcederStrategy(Agent):
    def __init__(self, name: str = "conceder", start: float = 0.85,
                 end: float = 0.40, noise: float = 0.0):
        self.name = name
        self.start = start
        self.end = end
        self.noise = noise
        # Safe defaults; overwritten by reset() before each match.
        self.rng = random.Random(0)
        self.total_rounds = 8

    def config(self) -> dict:
        """The params that define this strategy's behaviour (decision D-038).

        Two ConcederStrategy agents with different schedules/noise get distinct
        identities; the RNG seed is per-match state, not config, so it is excluded.
        """
        return {"start": self.start, "end": self.end, "noise": self.noise}

    def _target(self, obs: Observation) -> float:
        total = max(1, self.total_rounds)
        progress = min(1.0, max(0.0, (total - obs.rounds_left) / total))
        return obs.my_max * (self.start - (self.start - self.end) * progress)

    def _propose(self, obs: Observation, target: float) -> Offer:
        n = obs.n_issues
        fav = [max(range(len(obs.my_util[i])), key=lambda lv: obs.my_util[i][lv]) for i in range(n)]
        con = [min(range(len(obs.my_util[i])), key=lambda lv: obs.my_util[i][lv]) for i in range(n)]
        levels = list(fav)
        current = obs.my_max
        # Concede the cheapest issues (smallest personal loss) first, until we hit target.
        for i in sorted(range(n), key=lambda i: obs.my_util[i][fav[i]] - obs.my_util[i][con[i]]):
            if current <= target:
                break
            current -= obs.my_util[i][fav[i]] - obs.my_util[i][con[i]]
            levels[i] = con[i]
        if self.noise and self.rng.random() < self.noise:
            # Erratically take back a concession (behave greedier than promised).
            conceded = [i for i in range(n) if levels[i] == con[i] and con[i] != fav[i]]
            if conceded:
                j = self.rng.choice(conceded)
                levels[j] = fav[j]
        return Offer(tuple(levels))

    def act(self, obs: Observation) -> Action:
        target = self._target(obs)
        proposal = self._propose(obs, target)
        proposal_value = obs.my_value(proposal)
        standing = obs.standing_offer
        if standing is not None:
            standing_value = obs.my_value(standing)
            if standing_value >= proposal_value:
                return Action.accept("That works for me — deal.")
            if obs.rounds_left <= 1 and standing_value >= obs.my_max * self.end:
                return Action.accept("Fine, let's close on that.")
        return Action.make_offer(proposal, "Here's my proposal.")
