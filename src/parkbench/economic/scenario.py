"""Seeded 0/1-knapsack instances + an exact optimum solver (decision D-036).

A `KnapsackScenario` is N items, each with an integer `value` and `weight`, and an integer budget
`B`. The agent picks a subset whose total weight is within budget; the objective is to maximize
total value. The instance is generated purely from a seed so it regenerates identically every time
(reproducibility is the whole point — same seed ⇒ identical instance ⇒ identical score).

Item counts and ranges are chosen so the optimum is **non-trivial** (greedy-by-ratio is not always
optimal — the classic knapsack gap) yet **instant** to solve exactly:
  - N defaults to 12 items, so brute force is 2**12 = 4096 subsets, and the DP table is
    `N * (B+1)` cells (a few thousand). Both are trivial.
  - The budget is set to ~45% of the total weight, the regime where the value/weight tradeoff
    actually bites and greedy can miss the optimum.

`solve_optimum` runs the standard bounded DP; `optimal_value` returns just its max value. A brute
force (`brute_optimum`) is kept for cross-checking the DP on small instances in the tests.
"""

from __future__ import annotations

import itertools
import random
from dataclasses import dataclass


@dataclass(frozen=True)
class Item:
    value: int
    weight: int


@dataclass(frozen=True)
class KnapsackScenario:
    items: tuple[Item, ...]
    budget: int
    seed: int | None = None

    @property
    def n_items(self) -> int:
        return len(self.items)

    def total_weight(self, chosen) -> int:
        """Total weight of the chosen item indices."""
        return sum(self.items[i].weight for i in chosen)

    def total_value(self, chosen) -> int:
        """Total value of the chosen item indices."""
        return sum(self.items[i].value for i in chosen)

    def is_feasible(self, chosen) -> bool:
        """A choice is feasible when indices are valid, distinct, and within budget."""
        idx = list(chosen)
        if any(not isinstance(i, int) or i < 0 or i >= self.n_items for i in idx):
            return False
        if len(set(idx)) != len(idx):
            return False
        return self.total_weight(idx) <= self.budget


# Defaults: small enough that brute force (2**N) and DP (N*(B+1)) are both instant, large enough
# that the value/weight greedy heuristic is not always optimal (a genuine knapsack gap).
DEFAULT_N_ITEMS = 12
VALUE_RANGE = (5, 40)
WEIGHT_RANGE = (3, 25)
BUDGET_FRACTION = 0.45  # budget as a fraction of total weight — the regime where the tradeoff bites


def generate_scenario(
    seed: int,
    n_items: int = DEFAULT_N_ITEMS,
    value_range: tuple[int, int] = VALUE_RANGE,
    weight_range: tuple[int, int] = WEIGHT_RANGE,
    budget_fraction: float = BUDGET_FRACTION,
) -> KnapsackScenario:
    """Deterministically generate a knapsack instance from a seed.

    Same `seed` (and shape) ⇒ byte-identical instance. The budget is a fixed fraction of the total
    weight (floored), clamped to at least the lightest item's weight so at least one item always
    fits (no degenerate empty-only optimum).
    """
    rng = random.Random(seed)
    items = tuple(
        Item(rng.randint(*value_range), rng.randint(*weight_range)) for _ in range(n_items)
    )
    total_w = sum(it.weight for it in items)
    budget = int(total_w * budget_fraction)
    budget = max(budget, min(it.weight for it in items))  # ensure ≥1 item fits
    return KnapsackScenario(items, budget, seed)


def solve_optimum(scenario: KnapsackScenario) -> tuple[int, tuple[int, ...]]:
    """Exact 0/1-knapsack via bounded dynamic programming.

    Returns `(optimal_value, chosen_indices)`. Runs in `O(N * B)` time/space — trivial for the
    suite's sizes. The chosen set is recovered by backtracking the DP table.
    """
    n, B = scenario.n_items, scenario.budget
    # dp[i][w] = best value using items[0:i] within capacity w.
    dp = [[0] * (B + 1) for _ in range(n + 1)]
    for i in range(1, n + 1):
        v, wt = scenario.items[i - 1].value, scenario.items[i - 1].weight
        row, prev = dp[i], dp[i - 1]
        for w in range(B + 1):
            best = prev[w]
            if wt <= w:
                take = prev[w - wt] + v
                if take > best:
                    best = take
            row[w] = best
    # Backtrack to recover which items were taken.
    chosen: list[int] = []
    w = B
    for i in range(n, 0, -1):
        if dp[i][w] != dp[i - 1][w]:
            chosen.append(i - 1)
            w -= scenario.items[i - 1].weight
    chosen.sort()
    return dp[n][B], tuple(chosen)


def optimal_value(scenario: KnapsackScenario) -> int:
    """The exact achievable maximum value for the instance (the scoring ceiling)."""
    return solve_optimum(scenario)[0]


def brute_optimum(scenario: KnapsackScenario) -> int:
    """Exact optimum by exhaustive subset enumeration — used to cross-check the DP in tests."""
    best = 0
    idx = range(scenario.n_items)
    for r in range(scenario.n_items + 1):
        for combo in itertools.combinations(idx, r):
            if scenario.total_weight(combo) <= scenario.budget:
                best = max(best, scenario.total_value(combo))
    return best
