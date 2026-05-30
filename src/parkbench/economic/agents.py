"""Baseline agents for the economic (knapsack) ride (decision D-036).

Each ride owns its own agent interface (D-035). Here it is deliberately tiny: an `EconomicAgent`
is anything that, given a `KnapsackScenario`, returns the set of item indices it would take. A
pure function would do, but a small class lets the `random` baseline carry a seedable RNG so whole
suites stay reproducible (mirrors `agents/base.py` in the negotiation ride).

The four baselines use the **same names** as the negotiation ride's agents
(`random` / `greedy` / `heuristic` / `optimal`) on purpose: the radar roll-up (D-037) profiles one
shared agent name across both rides, so the names must line up.

  - `random`    — a feasible floor: shuffle items, take greedily until the budget would be blown.
  - `greedy`    — classic value/weight-ratio greedy; strong but not always optimal (the knapsack gap).
  - `heuristic` — greedy-by-ratio plus a single-item swap improvement pass; usually ≥ greedy.
  - `optimal`   — the exact DP optimum; the score ceiling (always 1.0).
"""

from __future__ import annotations

import abc
import random

from .scenario import KnapsackScenario, solve_optimum


class EconomicAgent(abc.ABC):
    """Given a knapsack scenario, choose a set of item indices to take.

    `name` is the agent's registry key (shared with the negotiation ride for the radar roll-up).
    `reset(seed)` re-seeds any RNG so a whole suite reproduces exactly; stateless agents may ignore
    it. `choose` must return an iterable of distinct, in-range item indices; the ride clamps any
    infeasible (over-budget / invalid) choice to a score of 0.
    """

    name: str = "economic-agent"

    def reset(self, seed: int = 0) -> None:
        self.rng = random.Random(seed)

    @abc.abstractmethod
    def choose(self, scenario: KnapsackScenario) -> tuple[int, ...]:
        """Return the chosen item indices for this scenario."""


def _greedy_by_ratio(scenario: KnapsackScenario) -> list[int]:
    """Take items in descending value/weight ratio while they still fit the remaining budget."""
    order = sorted(
        range(scenario.n_items),
        key=lambda i: (
            scenario.items[i].value / scenario.items[i].weight,
            scenario.items[i].value,
        ),
        reverse=True,
    )
    chosen: list[int] = []
    remaining = scenario.budget
    for i in order:
        if scenario.items[i].weight <= remaining:
            chosen.append(i)
            remaining -= scenario.items[i].weight
    return chosen


class RandomAgent(EconomicAgent):
    """Feasible floor: shuffle the items, then take greedily in that random order until full."""

    name = "random"

    def choose(self, scenario: KnapsackScenario) -> tuple[int, ...]:
        order = list(range(scenario.n_items))
        self.rng.shuffle(order)
        chosen: list[int] = []
        remaining = scenario.budget
        for i in order:
            if scenario.items[i].weight <= remaining:
                chosen.append(i)
                remaining -= scenario.items[i].weight
        return tuple(sorted(chosen))


class GreedyAgent(EconomicAgent):
    """Classic value/weight-ratio greedy — strong, but not always optimal (the knapsack gap)."""

    name = "greedy"

    def choose(self, scenario: KnapsackScenario) -> tuple[int, ...]:
        return tuple(sorted(_greedy_by_ratio(scenario)))


class HeuristicAgent(EconomicAgent):
    """Greedy-by-ratio, then a single local-improvement pass.

    After the ratio fill, try to swap one unchosen item in for one chosen item (or simply add an
    unchosen item that still fits) whenever it raises total value within budget. One pass is cheap
    and reliably lifts the heuristic at or above plain greedy without ever reaching for the DP.
    """

    name = "heuristic"

    def choose(self, scenario: KnapsackScenario) -> tuple[int, ...]:
        chosen = set(_greedy_by_ratio(scenario))
        items = scenario.items
        improved = True
        while improved:
            improved = False
            weight = sum(items[i].weight for i in chosen)
            # 1) Add any unchosen item that simply fits.
            for j in range(scenario.n_items):
                if j not in chosen and weight + items[j].weight <= scenario.budget:
                    chosen.add(j)
                    weight += items[j].weight
                    improved = True
            # 2) Swap one chosen item out for an unchosen one that raises value within budget.
            for j in range(scenario.n_items):
                if j in chosen:
                    continue
                for i in list(chosen):
                    new_weight = weight - items[i].weight + items[j].weight
                    if new_weight <= scenario.budget and items[j].value > items[i].value:
                        chosen.discard(i)
                        chosen.add(j)
                        weight = new_weight
                        improved = True
                        break
        return tuple(sorted(chosen))


class OptimalAgent(EconomicAgent):
    """The exact DP optimum — the scoring ceiling (always scores 1.0)."""

    name = "optimal"

    def choose(self, scenario: KnapsackScenario) -> tuple[int, ...]:
        return solve_optimum(scenario)[1]


AGENT_REGISTRY: dict[str, type[EconomicAgent]] = {
    "random": RandomAgent,
    "greedy": GreedyAgent,
    "heuristic": HeuristicAgent,
    "optimal": OptimalAgent,
}


def make_agent(name: str) -> EconomicAgent:
    try:
        return AGENT_REGISTRY[name]()
    except KeyError:
        raise ValueError(
            f"Unknown economic agent '{name}'. Choices: {', '.join(sorted(AGENT_REGISTRY))}"
        ) from None
