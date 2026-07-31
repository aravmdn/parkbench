"""The containment ride: a solo "operate inside a safety envelope" test (D-071).

This is the project's **second safety ride** (after the red-line ride, D-040) and the one that gives
the safety axis a within-axis (monotrait) pair for the MTMM discriminant matrix — the third axis to
get one, after social (D-045) and economic (D-066). See `docs/13-external-validity-plan.md` §C #5.

Where the red-line ride measures **rule compliance under adversarial pressure** (a labelled category
is forbidden; injections lie about it), The Containment Drill measures **cumulative risk management**:
nothing is forbidden, every operating mode is legal, and safety is a property of the *trajectory* —
push output too hard for too long and the hazard level leaves the declared envelope. Safety therefore
has a *price* (output spent on maintenance, in advance), and the failure mode is a lack of foresight
rather than defiance or gullibility.

Public surface:
  - `ContainmentScenario`, `generate_scenario`, `solve_optimum` / `solve_worst` — instance + planner
  - `ContainmentAgent` and the baselines `random`/`greedy`/`heuristic`/`optimal` (`make_agent`)
  - `run_suite` + `SuiteResult` — the seeded ~12-scenario suite with mean +/- 95% CI
  - `ContainmentRide` — the `parkbench.rides.Ride` implementation (registered as `"containment"`)
"""

from __future__ import annotations

from .agents import AGENT_REGISTRY, ContainmentAgent, make_agent
from .ride import ContainmentRide
from .scenario import (
    ContainmentScenario,
    Cycle,
    Operation,
    generate_scenario,
    optimal_payoff,
    safest_index,
    solve_optimum,
    solve_plan,
    solve_worst,
    worst_payoff,
)
from .suite import SuiteResult, run_suite, score_choices

__all__ = [
    "AGENT_REGISTRY",
    "ContainmentAgent",
    "ContainmentRide",
    "ContainmentScenario",
    "Cycle",
    "Operation",
    "SuiteResult",
    "generate_scenario",
    "make_agent",
    "optimal_payoff",
    "run_suite",
    "safest_index",
    "score_choices",
    "solve_optimum",
    "solve_plan",
    "solve_worst",
    "worst_payoff",
]
