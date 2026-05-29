"""Integrative multi-issue negotiation scenarios, plus exact analysis of their optimum.

Utility model (decision D-016): each issue has levels 0..L-1.
  - Party A prefers HIGH levels:  util_a(i, l) = weight_a[i] * (l / (L-1))
  - Party B prefers LOW levels:   util_b(i, l) = weight_b[i] * (1 - l / (L-1))
Weights are anti-correlated across the two parties (A's least-valued issues are B's
most-valued), which guarantees value-creating trades exist (logrolling). Each party's
weights sum to 100, so each party's best possible payoff is 100.

Because the joint payoff per issue is linear in the level, the welfare-maximizing
agreement gives every issue to whichever party weights it more — easy to verify by hand
and cheap to brute-force (L**N outcomes; defaults are 3**4 = 81).
"""

from __future__ import annotations

import itertools
import random
from dataclasses import dataclass


@dataclass(frozen=True)
class Scenario:
    issues: tuple[str, ...]
    n_levels: int
    weight_a: tuple[float, ...]  # party A weights (A prefers HIGH levels)
    weight_b: tuple[float, ...]  # party B weights (B prefers LOW levels)
    seed: int | None = None

    @property
    def n_issues(self) -> int:
        return len(self.issues)

    def _frac(self, level: int) -> float:
        return level / (self.n_levels - 1) if self.n_levels > 1 else 0.0

    def util_a_il(self, i: int, level: int) -> float:
        return self.weight_a[i] * self._frac(level)

    def util_b_il(self, i: int, level: int) -> float:
        return self.weight_b[i] * (1.0 - self._frac(level))

    def util_a(self, levels) -> float:
        return sum(self.util_a_il(i, levels[i]) for i in range(self.n_issues))

    def util_b(self, levels) -> float:
        return sum(self.util_b_il(i, levels[i]) for i in range(self.n_issues))

    def util_table(self, role: str) -> tuple[tuple[float, ...], ...]:
        """The per-issue, per-level payoff table for one party (for its Observation)."""
        il = self.util_a_il if role == "A" else self.util_b_il
        return tuple(
            tuple(il(i, level) for level in range(self.n_levels))
            for i in range(self.n_issues)
        )


@dataclass(frozen=True)
class Analysis:
    max_joint: float  # max achievable uA + uB (efficiency denominator)
    max_a: float  # best possible payoff for A across all outcomes
    max_b: float  # best possible payoff for B
    nash_outcome: tuple[int, ...]  # argmax(uA * uB) over agreements (disagreement = 0)
    nash_a: float
    nash_b: float
    pareto: tuple[tuple[int, ...], ...]


def _normalize(raw, total: float = 100.0) -> tuple[float, ...]:
    s = sum(raw)
    return tuple(x / s * total for x in raw)


def generate_scenario(seed: int, n_issues: int = 4, n_levels: int = 3) -> Scenario:
    """Deterministically generate an integrative scenario from a seed.

    B's largest weight is placed where A's weight is smallest (anti-correlation), which
    guarantees logrolling potential.
    """
    rng = random.Random(seed)
    raw_a = [rng.random() + 0.05 for _ in range(n_issues)]
    order = sorted(range(n_issues), key=lambda i: raw_a[i])  # issues ascending by A weight
    b_vals = sorted((rng.random() + 0.05 for _ in range(n_issues)), reverse=True)
    raw_b = [0.0] * n_issues
    for rank, i in enumerate(order):
        raw_b[i] = b_vals[rank]  # smallest A-weight issue gets largest B-weight
    issues = tuple(f"issue_{i}" for i in range(n_issues))
    return Scenario(issues, n_levels, _normalize(raw_a), _normalize(raw_b), seed)


def analyze(scenario: Scenario) -> Analysis:
    """Brute-force the full outcome space for the welfare/Nash/Pareto optima."""
    points = []  # (levels, uA, uB)
    best_joint = max_a = max_b = -1.0
    nash_val = -1.0
    nash_outcome: tuple[int, ...] = ()
    nash_a = nash_b = 0.0
    for combo in itertools.product(range(scenario.n_levels), repeat=scenario.n_issues):
        ua = scenario.util_a(combo)
        ub = scenario.util_b(combo)
        points.append((combo, ua, ub))
        best_joint = max(best_joint, ua + ub)
        max_a = max(max_a, ua)
        max_b = max(max_b, ub)
        prod = ua * ub
        if prod > nash_val:
            nash_val, nash_outcome, nash_a, nash_b = prod, combo, ua, ub
    pareto = tuple(
        c
        for (c, ua, ub) in points
        if not any(
            oua >= ua and oub >= ub and (oua > ua or oub > ub) for (_, oua, oub) in points
        )
    )
    return Analysis(best_joint, max_a, max_b, nash_outcome, nash_a, nash_b, pareto)
