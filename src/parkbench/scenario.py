"""Integrative multi-issue negotiation scenarios, plus exact analysis of their optimum.

Utility model (decision D-016): each issue has levels 0..L-1.
  - Party A prefers HIGH levels:  util_a(i, l) = weight_a[i] * (l / (L-1))
  - Party B prefers LOW levels:   util_b(i, l) = weight_b[i] * (1 - l / (L-1))
Weights are anti-correlated across the two parties (A's least-valued issues are B's
most-valued), which guarantees value-creating trades exist (logrolling). Each party's
weights sum to 100, so each party's best possible payoff is 100.

Because the joint payoff per issue is linear in the level, the welfare-maximizing
agreement gives every issue to whichever party weights it more — easy to verify by hand
and cheap to brute-force (L**N outcomes; the suite cycles shapes from 3x5 up to 5x5 = 3125).
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


# Suite-wide menu of scenario shapes (decision D-032). Cycling issue/level counts across
# the suite widens the outcome space the agent must navigate. Coarse 3-issue x 3-level
# scenarios leave too few distinct Pareto agreements, so personas with different acceptance
# floors were forced onto the SAME agreement; richer shapes (more issues, finer levels) give
# the floors room to land on genuinely different deals. All shapes stay inside D-016's 3-5
# issues; levels span 3-5 for finer trades. The largest (5 issues x 5 levels = 3125 outcomes)
# is still trivial to brute-force in analyze().
SCENARIO_SHAPES: tuple[tuple[int, int], ...] = (
    (4, 4),
    (5, 4),
    (4, 5),
    (5, 3),
    (5, 5),
    (4, 3),
    (3, 5),
    (5, 4),
)


def shape_for_index(index: int) -> tuple[int, int]:
    """Deterministically pick a (n_issues, n_levels) shape for a suite scenario index."""
    return SCENARIO_SHAPES[index % len(SCENARIO_SHAPES)]


def _spread_weights(rng: random.Random, n: int) -> list[float]:
    """Draw n raw weights with moderate, bounded dispersion.

    A base offset plus uniform jitter (`base + U(0, jit)`) keeps any single issue from
    dwarfing the rest: weights differ enough that issues are genuinely ranked, but no issue
    is so dominant that conceding it (the concession step is per-issue) hands the counterpart
    an almost-optimal deal in one move. That graduated structure is what lets the personas'
    acceptance floors produce distinguishable agreements (see `personas/house_cast.py`).
    Flat weights collapsed the breakdowns; heavily skewed (e.g. squared) weights collapsed
    them the other way by making one issue decisive.
    """
    base, jit = 0.5, 1.0
    return [base + rng.random() * jit for _ in range(n)]


def generate_scenario(seed: int, n_issues: int = 4, n_levels: int = 3) -> Scenario:
    """Deterministically generate an integrative scenario from a seed.

    Both parties get moderately dispersed weights (issues are ranked but none dominates);
    B's weights are then anti-aligned with A's — B's largest weight is placed where A's
    weight is smallest — which guarantees logrolling potential (decision D-016) while keeping
    the value-creating trades graduated enough to discriminate behavior (decision D-032).
    """
    rng = random.Random(seed)
    raw_a = _spread_weights(rng, n_issues)
    order = sorted(range(n_issues), key=lambda i: raw_a[i])  # issues ascending by A weight
    b_vals = sorted(_spread_weights(rng, n_issues), reverse=True)
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
