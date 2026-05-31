"""The safety ride: a solo red-line-under-adversarial-pressure test (decision D-040).

The project's **fourth** scored ride and the first on the **safety** axis (D-005), which **completes
the four-axis diagnostic radar** (D-007/D-037). It is a clean *solo* ride (D-006): an agent makes a
sequence of decisions, each round trading reward against a fixed **red-line rule**; some rounds carry
an adversarial **injection** (the "nudge as adversarial probe", D-003) that falsely claims the
forbidden option is authorized. Crossing a red line zeroes the scenario regardless of reward, so the
headline score (normalized to ``[0, 1]`` like every ride, D-035) rewards capability *and* safety —
and the baselines form a capability ladder where naive reward maximization (greedy) is exposed as a
reward-hacker.

Public surface:
  - `SafetyScenario`, `generate_scenario`, `optimal_safe_value`, `score_choices` — the instance + scoring
  - `SafetyAgent` and the baselines `random`/`greedy`/`heuristic`/`optimal` (`make_agent`)
  - `run_suite` + `SuiteResult` — the seeded suite with mean ± 95% CI + violation rate + per-type means
  - `SafetyRide` — the `parkbench.rides.Ride` implementation (registered as `"safety"`)
"""

from __future__ import annotations

from .agents import AGENT_REGISTRY, SafetyAgent, make_agent
from .ride import SafetyRide
from .scenario import (
    Action,
    Injection,
    Round,
    SafetyScenario,
    generate_scenario,
    optimal_safe_value,
    score_choices,
)
from .suite import SuiteResult, run_suite, scenario_type

__all__ = [
    "Action",
    "Injection",
    "Round",
    "SafetyScenario",
    "generate_scenario",
    "optimal_safe_value",
    "score_choices",
    "SafetyAgent",
    "AGENT_REGISTRY",
    "make_agent",
    "SuiteResult",
    "run_suite",
    "scenario_type",
    "SafetyRide",
]
