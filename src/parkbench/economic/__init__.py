"""The economic ride: a solo resource-allocation (knapsack) test (decision D-036).

This is the project's **second** scored ride and the first on the **economic** axis (D-005),
added so the diagnostic radar (D-007/D-037) has ≥2 axes to plot. Where the negotiation ride
(`social` axis) is multi-agent, this one is deliberately **solo** and deterministic: an agent is
handed a seeded 0/1-knapsack instance (items with integer `value`/`weight`, a budget `B`) and
returns the item set it would take. Scoring is the achieved value over the exact optimum, so the
headline score is normalized to `[0, 1]` exactly like every other ride (D-035) — `optimal` play
scores 1.0 by construction, a `random` floor gives context.

Public surface:
  - `KnapsackScenario`, `generate_scenario`, `optimal_value` / `solve_optimum` — the instance + solver
  - `EconomicAgent` and the baselines `random`/`greedy`/`heuristic`/`optimal` (`make_agent`)
  - `run_suite` + `SuiteResult` — the seeded ~12-scenario suite with mean ± 95% CI
  - `EconomicRide` — the `parkbench.rides.Ride` implementation (registered as `"economic"`)
"""

from __future__ import annotations

from .agents import AGENT_REGISTRY, EconomicAgent, make_agent
from .ride import EconomicRide
from .scenario import KnapsackScenario, generate_scenario, optimal_value, solve_optimum
from .suite import SuiteResult, run_suite, score_allocation

__all__ = [
    "KnapsackScenario",
    "generate_scenario",
    "optimal_value",
    "solve_optimum",
    "EconomicAgent",
    "AGENT_REGISTRY",
    "make_agent",
    "SuiteResult",
    "run_suite",
    "score_allocation",
    "EconomicRide",
]
