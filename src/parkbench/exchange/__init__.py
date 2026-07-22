"""The exchange ride: a solo allocative-efficiency (assignment / max-weight matching) test (D-066).

This is the project's **second economic ride** (after the knapsack, D-036) and the one that finally
gives the economic axis a within-axis (monotrait) pair for the MTMM discriminant matrix, while
widening the economic axis' dynamic range with a lower random floor (see
`docs/13-external-validity-plan.md`). Where the knapsack measures *selection under a scarce budget*
(what to take), The Exchange measures **allocative efficiency** (who gets what) — the canonical
matching-market problem — via a **maximum-weight assignment**, scored on a best/worst-response bracket.

Public surface:
  - `ExchangeScenario`, `generate_scenario`, `solve_optimum` / `solve_worst` — the instance + solver
  - `ExchangeAgent` and the baselines `random`/`greedy`/`heuristic`/`optimal` (`make_agent`)
  - `run_suite` + `SuiteResult` — the seeded ~12-scenario suite with mean +/- 95% CI
  - `ExchangeRide` — the `parkbench.rides.Ride` implementation (registered as `"exchange"`)
"""

from __future__ import annotations

from .agents import AGENT_REGISTRY, ExchangeAgent, make_agent
from .ride import ExchangeRide
from .scenario import (
    ExchangeScenario,
    generate_scenario,
    optimal_surplus,
    solve_optimum,
    solve_worst,
    worst_surplus,
)
from .suite import SuiteResult, run_suite, score_assignment

__all__ = [
    "ExchangeScenario",
    "generate_scenario",
    "optimal_surplus",
    "worst_surplus",
    "solve_optimum",
    "solve_worst",
    "ExchangeAgent",
    "AGENT_REGISTRY",
    "make_agent",
    "SuiteResult",
    "run_suite",
    "score_assignment",
    "ExchangeRide",
]
