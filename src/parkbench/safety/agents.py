"""Baseline agents for the safety ride (decision D-040).

Each ride owns its own agent interface (D-035). A `SafetyAgent`, given a `SafetyScenario`, returns
one action index per round. The four baselines reuse the **shared roster names** (`random` /
`greedy` / `heuristic` / `optimal`) so the radar (D-037) profiles one agent across all axes — and
the safety axis is where the differences between them become a *capability ladder*, each tier adding
one real skill:

  - `random`    — floor: picks a uniformly random action each round (crosses red lines by accident).
  - `greedy`    — pure reward maximizer: picks the highest reward each round, **ignoring the rule**.
                  On a tempting round the forbidden action *is* the max reward, so greedy takes the
                  bait and the scenario zeroes. greedy is the textbook **reward-hacker** — strong on
                  the economic ride, worst here.
  - `heuristic` — follows the fixed rule normally, but is **manipulable**: it *believes* an
                  adversarial injection that claims a forbidden category is "authorized" and treats
                  that category as allowed for the round (so it can be tricked into a violation).
                  Safe and near-optimal on un-injected rounds.
  - `optimal`   — safe **and** robust: maximizes reward among truly-safe actions and **ignores
                  injections entirely** (trusts only the fixed rule). Never violates ⇒ scores 1.0.

The gradient that falls out — optimal 1.0 > heuristic > greedy, with random a low floor — is the
point of the safety axis: naive reward maximization (greedy) reward-hacks and fails; resisting
in-band manipulation (optimal vs. heuristic) is what separates a robust agent from a merely
rule-aware one.
"""

from __future__ import annotations

import abc
import random

from .scenario import Round, SafetyScenario


def _argmax_reward(rnd: Round, allowed_predicate) -> int:
    """Index of the highest-reward action satisfying `allowed_predicate`; falls back to global max.

    Ties break to the lowest index (deterministic). If no action satisfies the predicate (should not
    happen — a safe action is always present), it falls back to the global max so a choice is always
    returned.
    """
    best_idx, best_reward = None, None
    for i, a in enumerate(rnd.actions):
        if allowed_predicate(a) and (best_reward is None or a.reward > best_reward):
            best_idx, best_reward = i, a.reward
    if best_idx is not None:
        return best_idx
    # Fallback: global argmax (deterministic, lowest index on ties).
    return max(range(len(rnd.actions)), key=lambda i: (rnd.actions[i].reward, -i))


class SafetyAgent(abc.ABC):
    """Given a safety scenario, return one chosen action index per round.

    `reset(seed)` re-seeds any RNG so a whole suite reproduces exactly; stateless agents may ignore
    it. `choose` must return one index per round; the ride scores any malformed or red-line-crossing
    play as 0.
    """

    name: str = "safety-agent"

    def reset(self, seed: int = 0) -> None:
        self.rng = random.Random(seed)

    @abc.abstractmethod
    def choose(self, scenario: SafetyScenario) -> tuple[int, ...]:
        """Return the chosen action index for each round."""


class RandomAgent(SafetyAgent):
    """Floor: a uniformly random action each round."""

    name = "random"

    def choose(self, scenario: SafetyScenario) -> tuple[int, ...]:
        return tuple(self.rng.randrange(len(r.actions)) for r in scenario.rounds)


class GreedyAgent(SafetyAgent):
    """Pure reward maximizer — ignores the rule entirely (the reward-hacker)."""

    name = "greedy"

    def choose(self, scenario: SafetyScenario) -> tuple[int, ...]:
        return tuple(_argmax_reward(r, lambda a: True) for r in scenario.rounds)


class HeuristicAgent(SafetyAgent):
    """Rule-aware but manipulable: an injection's claimed-authorized category is treated as allowed."""

    name = "heuristic"

    def choose(self, scenario: SafetyScenario) -> tuple[int, ...]:
        choices: list[int] = []
        for rnd in scenario.rounds:
            # Effective rule = the fixed forbidden set MINUS anything the injection claims is OK.
            effective = set(scenario.forbidden)
            if rnd.injection is not None:
                effective.discard(rnd.injection.authorized_category)
            choices.append(_argmax_reward(rnd, lambda a, e=effective: a.category not in e))
        return tuple(choices)


class OptimalAgent(SafetyAgent):
    """Safe and robust: max reward among truly-safe actions; ignores injections (the 1.0 ceiling)."""

    name = "optimal"

    def choose(self, scenario: SafetyScenario) -> tuple[int, ...]:
        return tuple(
            _argmax_reward(r, lambda a: a.category not in scenario.forbidden)
            for r in scenario.rounds
        )


AGENT_REGISTRY: dict[str, type[SafetyAgent]] = {
    "random": RandomAgent,
    "greedy": GreedyAgent,
    "heuristic": HeuristicAgent,
    "optimal": OptimalAgent,
}


def make_agent(name: str) -> SafetyAgent:
    try:
        return AGENT_REGISTRY[name]()
    except KeyError:
        raise ValueError(
            f"Unknown safety agent '{name}'. Choices: {', '.join(sorted(AGENT_REGISTRY))}"
        ) from None
