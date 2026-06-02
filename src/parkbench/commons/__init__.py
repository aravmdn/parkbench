"""The commons ride: a multi-agent repeated public-goods (cooperation) test (decision D-045).

This is the project's **fifth** scored ride and the **second on the social axis** (D-005) — the first
time two rides share an axis, exercising the radar's per-axis mean (D-037). Where the negotiation ride
measures bilateral bargaining, this one measures **cooperation under a social dilemma**: an agent
plays a finitely-repeated public-goods game against a fixed, deterministic **house cast** (D-004) in
which free-riding is individually tempting but the welfare optimum is cooperation. The skill scored is
*eliciting and sustaining* the society's cooperation — only a reactive house member makes cooperating
pay, so a pure free-rider gets retaliated against and finishes worst.

Scoring is the achieved total payoff normalized onto ``[0, 1]`` against the exact best/worst response
to the fixed cast (brute-forced), so `optimal` play scores 1.0 by construction and the scale is
gaming-resistant — the same objective-payoff-vs-baselines backbone as every other ride (D-011/D-019).

Public surface:
  - `CommonsScenario`, `generate_scenario`, `simulate`, `solve_response_bounds`, `score_total`
  - `CommonsAgent` and the baselines `random`/`greedy`/`heuristic`/`optimal` (`make_agent`)
  - `run_suite` + `SuiteResult` — the seeded ~12-game suite with mean ± 95% CI
  - `CommonsRide` — the `parkbench.rides.Ride` implementation (registered as `"commons"`)
"""

from __future__ import annotations

from .agents import AGENT_REGISTRY, CommonsAgent, make_agent
from .ride import CommonsRide
from .scenario import (
    CommonsScenario,
    ResponseBounds,
    generate_scenario,
    score_total,
    simulate,
    solve_response_bounds,
)
from .suite import SuiteResult, run_suite

__all__ = [
    "CommonsScenario",
    "ResponseBounds",
    "generate_scenario",
    "simulate",
    "solve_response_bounds",
    "score_total",
    "CommonsAgent",
    "AGENT_REGISTRY",
    "make_agent",
    "SuiteResult",
    "run_suite",
    "CommonsRide",
]
