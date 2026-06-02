"""Baseline agents for the commons (public-goods) ride (decision D-045).

Each ride owns its own agent interface (D-035). A `CommonsAgent` chooses, round by round, how much to
contribute to the common pool, given the history of every player's past contributions (so a reactive
agent can condition on what the society did). The four baselines reuse the **shared roster names**
(`random` / `greedy` / `heuristic` / `optimal`) so the radar (D-037) profiles one agent across both
social rides — and the commons axis is where naive free-riding gets *punished by the society*:

  - `random`    — floor-ish: a uniformly random contribution level each round (erratic; trips the
                  reciprocator's trigger unpredictably).
  - `greedy`    — pure free-rider: contributes **0** every round. The textbook reward-hacker again —
                  it grabs the common pool without paying in, so the reciprocator retaliates from
                  round 1 and greedy ends up **below** even random (which sometimes cooperates early
                  and keeps the pool alive). Strong on the economic ride, worst here.
  - `heuristic` — a reciprocating conditional cooperator: meets the cooperation bar (contributes the
                  threshold) as long as the society cooperated last round, else withholds. Sustains
                  the reciprocator's cooperation, so it scores well — but it over-pays slightly and
                  never exploits the endgame, so it sits below optimal.
  - `optimal`   — replays the exact **best response** to the fixed cast (brute-forced once): cooperate
                  just enough to keep the reciprocator, then defect on the final round when there is no
                  future left to protect (backward-induction endgame). Scores 1.0 by construction.

The gradient that falls out — optimal 1.0 > heuristic > random > greedy — is the point of the second
social ride: it generalizes the reward-hacker story from the safety axis to *cooperation*, where a
society that reciprocates makes pure exploitation the worst policy.
"""

from __future__ import annotations

import abc
import random

from .scenario import CommonsScenario, solve_response_bounds


class CommonsAgent(abc.ABC):
    """Given the game and the history so far, choose this round's contribution.

    `name` is the agent's registry key (shared across rides for the radar roll-up). `reset(seed)`
    re-seeds any RNG so a whole suite reproduces exactly; stateless agents may ignore it. `contribute`
    returns an integer in ``[0, endowment]`` (the game clamps anything out of range).
    """

    name: str = "commons-agent"

    def reset(self, seed: int = 0) -> None:
        self.rng = random.Random(seed)

    @abc.abstractmethod
    def contribute(self, round_idx: int, history: list[tuple[int, ...]], scenario: CommonsScenario) -> int:
        """Return A's contribution for ``round_idx`` given the full per-round history so far."""


class RandomAgent(CommonsAgent):
    """Floor: a uniformly random contribution level ({none, half, full}) each round."""

    name = "random"

    def contribute(self, round_idx, history, scenario) -> int:
        return self.rng.choice(scenario.levels)


class GreedyAgent(CommonsAgent):
    """Pure free-rider: contributes nothing, ever (the reward-hacker — punished by reciprocity)."""

    name = "greedy"

    def contribute(self, round_idx, history, scenario) -> int:
        return 0


class HeuristicAgent(CommonsAgent):
    """Reciprocating conditional cooperator: meet the bar while the society cooperates.

    Round 0: contribute the cooperation threshold (signal willingness). Thereafter: if the *other*
    players' mean contribution last round was at least the threshold, keep contributing the threshold
    (sustaining the reciprocator); otherwise withhold (contribute 0). Meets the bar without
    over-paying, but never exploits the final round — so it lands between greedy and optimal.
    """

    name = "heuristic"

    def contribute(self, round_idx, history, scenario) -> int:
        if round_idx == 0 or not history:
            return scenario.threshold
        others = history[-1][1:]  # everyone except A, last round
        mean_others = sum(others) / len(others) if others else 0.0
        return scenario.threshold if mean_others >= scenario.threshold else 0


class OptimalAgent(CommonsAgent):
    """Replays the exact best-response sequence to the fixed cast — the 1.0 ceiling.

    The best response against a deterministic cast is an open-loop sequence, so it is computed once
    (brute-forced by `solve_response_bounds`) and replayed by round index; history is ignored. The
    sequence is memoized per scenario seed so a whole suite stays cheap.
    """

    name = "optimal"

    def __init__(self) -> None:
        self._cache: dict[int | None, tuple[int, ...]] = {}

    def contribute(self, round_idx, history, scenario) -> int:
        key = scenario.seed
        seq = self._cache.get(key)
        if seq is None:
            seq = solve_response_bounds(scenario).best_sequence
            self._cache[key] = seq
        return seq[round_idx]


AGENT_REGISTRY: dict[str, type[CommonsAgent]] = {
    "random": RandomAgent,
    "greedy": GreedyAgent,
    "heuristic": HeuristicAgent,
    "optimal": OptimalAgent,
}


def make_agent(name: str) -> CommonsAgent:
    try:
        return AGENT_REGISTRY[name]()
    except KeyError:
        raise ValueError(
            f"Unknown commons agent '{name}'. Choices: {', '.join(sorted(AGENT_REGISTRY))}"
        ) from None
