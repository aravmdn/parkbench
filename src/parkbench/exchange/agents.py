"""Baseline agents for the exchange (assignment) ride (decision D-066).

Each ride owns its own agent interface (D-035). An `ExchangeAgent` is anything that, given an
`ExchangeScenario`, returns a **permutation** ``σ`` — a tuple where ``σ[i]`` is the good assigned to
trader *i*. A pure function would do, but a small class lets the `random` baseline carry a seedable
RNG so whole suites stay reproducible (mirrors the knapsack ride's `EconomicAgent`, D-036).

The four baselines reuse the **shared roster names** (`random` / `greedy` / `heuristic` / `optimal`)
so the radar (D-037) can profile one agent across *both* economic rides — and, since both economic
rides ship an `optimal`, the MTMM matrix can finally correlate the economic axis over all four
baselines (docs/13 §A.5). They are the direct allocative analogues of the knapsack baselines:

  - `random`    — a uniformly random valid permutation (the feasible floor).
  - `greedy`    — **myopic** matching: process traders in index order, assigning each its
                  highest-surplus still-available good. Strong but not globally optimal (the analogue
                  of the knapsack's ratio-greedy and its "gap").
  - `heuristic` — `greedy` plus a **2-swap local-improvement pass**: repeatedly swap two traders'
                  goods whenever it raises total surplus (mirrors the knapsack heuristic's swap pass);
                  usually >= greedy.
  - `optimal`   — the exact max-weight matching; the 1.0 ceiling by construction.
"""

from __future__ import annotations

import abc
import random

from .scenario import ExchangeScenario, solve_optimum


class ExchangeAgent(abc.ABC):
    """Given an assignment scenario, choose a permutation of goods to traders.

    `name` is the agent's registry key (shared across rides for the radar roll-up). `reset(seed)`
    re-seeds any RNG so a whole suite reproduces exactly; stateless agents may ignore it. `choose`
    must return a permutation of ``range(N)`` (a tuple ``σ`` with ``σ[i]`` = trader *i*'s good); the
    ride scores any malformed (non-permutation) choice as 0.
    """

    name: str = "exchange-agent"

    def reset(self, seed: int = 0) -> None:
        self.rng = random.Random(seed)

    @abc.abstractmethod
    def choose(self, scenario: ExchangeScenario) -> tuple[int, ...]:
        """Return the chosen assignment (a permutation of good indices, one per trader)."""


def _greedy_match(scenario: ExchangeScenario) -> list[int]:
    """Myopic matching: each trader (in index order) grabs its best still-available good."""
    n = scenario.n
    available = set(range(n))
    assignment = [0] * n
    for i in range(n):
        # Highest surplus among available goods; ties break to the lowest good index (determinism).
        good = max(available, key=lambda j: (scenario.surplus[i][j], -j))
        assignment[i] = good
        available.discard(good)
    return assignment


class RandomAgent(ExchangeAgent):
    """Feasible floor: a uniformly random valid permutation of goods to traders."""

    name = "random"

    def choose(self, scenario: ExchangeScenario) -> tuple[int, ...]:
        order = list(range(scenario.n))
        self.rng.shuffle(order)
        return tuple(order)


class GreedyAgent(ExchangeAgent):
    """Myopic matching — strong, but not globally optimal (the assignment gap)."""

    name = "greedy"

    def choose(self, scenario: ExchangeScenario) -> tuple[int, ...]:
        return tuple(_greedy_match(scenario))


class HeuristicAgent(ExchangeAgent):
    """Greedy matching, then a **2-swap local-improvement** pass.

    After the myopic fill, repeatedly try swapping the goods of two traders whenever the swap raises
    total surplus, until no improving swap remains. A pure permutation swap keeps the assignment
    feasible by construction, and the pass reliably lifts the heuristic at or above plain greedy
    without reaching for the exact solver (mirrors the knapsack heuristic's swap pass, D-036).
    """

    name = "heuristic"

    def choose(self, scenario: ExchangeScenario) -> tuple[int, ...]:
        n = scenario.n
        assignment = _greedy_match(scenario)
        V = scenario.surplus
        improved = True
        while improved:
            improved = False
            for a in range(n):
                for b in range(a + 1, n):
                    ga, gb = assignment[a], assignment[b]
                    before = V[a][ga] + V[b][gb]
                    after = V[a][gb] + V[b][ga]
                    if after > before:
                        assignment[a], assignment[b] = gb, ga
                        improved = True
        return tuple(assignment)


class OptimalAgent(ExchangeAgent):
    """The exact max-weight matching — the scoring ceiling (always scores 1.0)."""

    name = "optimal"

    def choose(self, scenario: ExchangeScenario) -> tuple[int, ...]:
        return solve_optimum(scenario)[1]


AGENT_REGISTRY: dict[str, type[ExchangeAgent]] = {
    "random": RandomAgent,
    "greedy": GreedyAgent,
    "heuristic": HeuristicAgent,
    "optimal": OptimalAgent,
}


def make_agent(name: str) -> ExchangeAgent:
    try:
        return AGENT_REGISTRY[name]()
    except KeyError:
        raise ValueError(
            f"Unknown exchange agent '{name}'. Choices: {', '.join(sorted(AGENT_REGISTRY))}"
        ) from None
