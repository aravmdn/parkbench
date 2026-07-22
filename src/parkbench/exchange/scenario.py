"""Seeded assignment ("The Exchange") instances + an exact max/min-weight matching solver (D-066).

The Exchange is the project's **second economic ride** and the first to measure **allocative
efficiency** rather than selection-under-a-budget (the knapsack ride, D-036). Where the knapsack asks
*what to take*, this asks *who gets what* — the canonical matching-market problem. Selection-DP and
permutation-matching are genuinely distinct problem structures, which is the whole point: a high
correlation between the two economic rides is then real convergent evidence, not two runs of the same
solver (see `docs/13-external-validity-plan.md`).

An `ExchangeScenario` is an ``N x N`` integer **surplus matrix** ``V[i][j]`` — the value trader *i*
realizes from good *j*. A choice is a **permutation** ``σ`` assigning each trader one distinct good;
the objective is to maximize total surplus ``Σ_i V[i][σ(i)]``. The instance is generated purely from a
seed so it regenerates identically every time (reproducibility is the whole point — same seed ⇒
byte-identical matrix ⇒ identical score).

``N`` defaults to 7 (so ``N! = 5040`` permutations — brute force is instant and cross-checks the exact
solver in tests), small enough that the ``O(N^3)`` Hungarian algorithm is trivial. Unlike the
knapsack's ``achieved/optimal`` score, this ride is scored on a **best/worst-response bracket** (see
``suite.py``), which needs *both* the max-weight matching (the ceiling) and the **min**-weight matching
(the floor) — hence ``solve_optimum`` and ``solve_worst``. Both go through one general assignment
solver (``_hungarian_min``, an ``O(N^3)`` potentials-based Kuhn–Munkres), cross-checked against
exhaustive permutation search on small instances in the tests, exactly as the knapsack DP is
cross-checked against ``brute_optimum``.

The value range / ``N`` are exposed as generator parameters (a difficulty knob from day one, per
`docs/13` §A.2): a wider spread of surpluses gives a random permutation a materially *lower* bracket
floor than the knapsack's, widening the economic axis's measurable range.
"""

from __future__ import annotations

import itertools
import random
from dataclasses import dataclass

# Defaults: N small enough that brute force (N!) cross-checks the O(N^3) solver instantly, large
# enough that greedy myopic matching is not always optimal (a genuine assignment gap), and a wide
# value range so a random permutation captures far less of the surplus spread than the optimum — the
# deliberately-low bracket floor that widens the economic axis (docs/13 §A.2).
DEFAULT_N_TRADERS = 7
VALUE_RANGE = (1, 20)


@dataclass(frozen=True)
class ExchangeScenario:
    """One assignment instance: an ``N x N`` integer surplus matrix (D-066).

    ``surplus[i][j]`` is the value trader *i* gets from good *j*. A choice is a permutation ``σ`` (a
    tuple of length ``N``) where ``σ[i]`` is the good assigned to trader *i*. Fully seed-derived.
    """

    surplus: tuple[tuple[int, ...], ...]
    seed: int | None = None

    @property
    def n(self) -> int:
        return len(self.surplus)

    def total_surplus(self, assignment) -> int:
        """Total surplus ``Σ_i V[i][σ(i)]`` for an assignment (assumed valid; call `is_valid` first)."""
        return sum(self.surplus[i][assignment[i]] for i in range(self.n))

    def is_valid(self, assignment) -> bool:
        """A choice is valid iff it is a genuine permutation of ``range(N)`` (each good once)."""
        idx = list(assignment)
        if len(idx) != self.n:
            return False
        if any(not isinstance(j, int) or j < 0 or j >= self.n for j in idx):
            return False
        return len(set(idx)) == self.n


def generate_scenario(
    seed: int,
    n_traders: int = DEFAULT_N_TRADERS,
    value_range: tuple[int, int] = VALUE_RANGE,
) -> ExchangeScenario:
    """Deterministically generate an assignment instance from a seed.

    Same ``seed`` (and shape) ⇒ byte-identical matrix. Each cell is an independent integer surplus
    drawn uniformly from ``value_range`` — a wide range so the max- and min-weight matchings are far
    apart and a random permutation sits well inside the bracket (a low floor, docs/13 §A.2).
    """
    rng = random.Random(seed)
    lo, hi = value_range
    surplus = tuple(
        tuple(rng.randint(lo, hi) for _ in range(n_traders)) for _ in range(n_traders)
    )
    return ExchangeScenario(surplus=surplus, seed=seed)


# --------------------------------------------------------------------------------------------------
# Exact assignment solver — an O(N^3) Kuhn–Munkres (Hungarian) with potentials, minimizing total cost.
#
# The classic shortest-augmenting-path formulation (e-maxx). Returns a *perfect* min-cost matching of
# rows to distinct columns for any square real cost matrix (negative entries fine). Both the max- and
# min-weight surplus matchings reduce to it: max-surplus is min-cost on ``M − V`` (M any upper bound),
# min-surplus is min-cost on ``V`` itself. Cross-checked against exhaustive permutation search in the
# tests, exactly as the knapsack DP is cross-checked against brute force (D-036).
# --------------------------------------------------------------------------------------------------


def _hungarian_min(cost) -> tuple[int, tuple[int, ...]]:
    """Min-cost perfect assignment of an ``N x N`` cost matrix. Returns ``(min_total, assignment)``.

    ``assignment[i]`` is the column matched to row ``i``. ``O(N^3)`` time. Works for any integer costs
    (the algorithm's potentials handle negative values), so the ``M − V`` reduction for max-weight is
    safe. Deterministic (no RNG): a given matrix always yields the same optimal assignment.
    """
    n = len(cost)
    if n == 0:
        return 0, ()
    INF = float("inf")
    # u, v: dual potentials; p[j]: row matched to column j (1-indexed, column 0 is a virtual sentinel).
    u = [0.0] * (n + 1)
    v = [0.0] * (n + 1)
    p = [0] * (n + 1)
    way = [0] * (n + 1)
    for i in range(1, n + 1):
        p[0] = i
        j0 = 0
        minv = [INF] * (n + 1)
        used = [False] * (n + 1)
        while True:
            used[j0] = True
            i0 = p[j0]
            delta = INF
            j1 = -1
            for j in range(1, n + 1):
                if not used[j]:
                    cur = cost[i0 - 1][j - 1] - u[i0] - v[j]
                    if cur < minv[j]:
                        minv[j] = cur
                        way[j] = j0
                    if minv[j] < delta:
                        delta = minv[j]
                        j1 = j
            for j in range(n + 1):
                if used[j]:
                    u[p[j]] += delta
                    v[j] -= delta
                else:
                    minv[j] -= delta
            j0 = j1
            if p[j0] == 0:
                break
        while j0:
            j1 = way[j0]
            p[j0] = p[j1]
            j0 = j1
    assignment = [0] * n
    for j in range(1, n + 1):
        if p[j] != 0:
            assignment[p[j] - 1] = j - 1
    total = sum(cost[i][assignment[i]] for i in range(n))
    return total, tuple(assignment)


def solve_matching(scenario: ExchangeScenario, maximize: bool) -> tuple[int, tuple[int, ...]]:
    """Exact max- or min-weight perfect matching. Returns ``(total_surplus, assignment)``.

    Maximization reduces to a min-cost assignment on ``M − V`` (``M`` = the matrix max, so costs stay
    non-negative); minimization is a min-cost assignment on ``V`` directly. The returned surplus is
    recomputed from the *real* matrix so it is exact regardless of the reduction.
    """
    n = scenario.n
    if n == 0:
        return 0, ()
    if maximize:
        m = max(max(row) for row in scenario.surplus)
        cost = [[m - scenario.surplus[i][j] for j in range(n)] for i in range(n)]
    else:
        cost = [list(row) for row in scenario.surplus]
    _total, assignment = _hungarian_min(cost)
    return scenario.total_surplus(assignment), assignment


def solve_optimum(scenario: ExchangeScenario) -> tuple[int, tuple[int, ...]]:
    """The exact **max-weight** matching (the scoring ceiling): ``(max_surplus, assignment)``."""
    return solve_matching(scenario, maximize=True)


def solve_worst(scenario: ExchangeScenario) -> tuple[int, tuple[int, ...]]:
    """The exact **min-weight** matching (the bracket floor): ``(min_surplus, assignment)``."""
    return solve_matching(scenario, maximize=False)


def optimal_surplus(scenario: ExchangeScenario) -> int:
    """The maximum achievable total surplus for the instance (the scoring ceiling)."""
    return solve_optimum(scenario)[0]


def worst_surplus(scenario: ExchangeScenario) -> int:
    """The minimum achievable total surplus for the instance (the bracket floor)."""
    return solve_worst(scenario)[0]


def brute_optimum(scenario: ExchangeScenario) -> int:
    """Max total surplus by exhaustive permutation search — cross-checks the solver in tests."""
    return max(
        sum(scenario.surplus[i][perm[i]] for i in range(scenario.n))
        for perm in itertools.permutations(range(scenario.n))
    )


def brute_worst(scenario: ExchangeScenario) -> int:
    """Min total surplus by exhaustive permutation search — cross-checks the solver in tests."""
    return min(
        sum(scenario.surplus[i][perm[i]] for i in range(scenario.n))
        for perm in itertools.permutations(range(scenario.n))
    )
