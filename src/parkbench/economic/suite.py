"""The fixed economic-ride suite + per-scenario scoring (decision D-036).

Scoring (D-019-style: objective payoff vs. an exact optimum):

    score = achieved_value / optimal_value   in [0, 1]

`optimal_value` is the exact DP ceiling, so `optimal` play scores 1.0 by construction. An
**infeasible** choice (over budget, out-of-range, or duplicate indices) scores **0** — there is no
partial credit for an invalid allocation. The score is clamped to [0, 1] defensively.

A *score* over the ride is the mean of the per-scenario scores across a fixed suite of ~12 seeded
instances, reported with a 95% CI (reusing `scoring.Stat`, exactly as the negotiation ride does, so
the variance — the reproducibility evidence — is reported the same way across rides). Everything is
seed-derived, so the same suite seed ⇒ identical instances ⇒ identical scores.
"""

from __future__ import annotations

from dataclasses import dataclass

from ..scoring import Stat
from .agents import EconomicAgent
from .scenario import KnapsackScenario, generate_scenario, optimal_value

DEFAULT_N_SCENARIOS = 12


def score_allocation(scenario: KnapsackScenario, chosen, optimum: int | None = None) -> float:
    """Score one allocation: achieved_value / optimal_value, clamped to [0, 1]; 0 if infeasible."""
    if not scenario.is_feasible(chosen):
        return 0.0
    opt = optimal_value(scenario) if optimum is None else optimum
    if opt <= 0:
        return 0.0
    return max(0.0, min(1.0, scenario.total_value(chosen) / opt))


@dataclass
class ScenarioScore:
    scenario_seed: int | None
    n_items: int
    budget: int
    optimal_value: int
    achieved_value: int
    feasible: bool
    score: float


@dataclass
class SuiteResult:
    agent_name: str
    score: Stat  # mean ± 95% CI of per-scenario achieved/optimal
    feasible_rate: float  # fraction of scenarios with a feasible (non-zero-by-default) allocation
    scenarios: list  # list[ScenarioScore] — the per-scenario breakdown


def build_scenarios(seed: int, n_scenarios: int = DEFAULT_N_SCENARIOS) -> list[KnapsackScenario]:
    """The fixed suite: `n_scenarios` instances derived deterministically from the suite seed."""
    return [generate_scenario(seed + s) for s in range(n_scenarios)]


def run_suite(
    agent: EconomicAgent, seed: int = 1, n_scenarios: int = DEFAULT_N_SCENARIOS
) -> SuiteResult:
    """Run an economic agent through the fixed suite and aggregate its profile.

    Each scenario re-seeds the agent deterministically (so the `random` baseline is reproducible)
    before asking it to `choose`. The optimum is solved once per scenario and shared with scoring.
    """
    scenarios = build_scenarios(seed, n_scenarios)
    rows: list[ScenarioScore] = []
    for idx, scenario in enumerate(scenarios):
        agent.reset(seed=seed * 1_000_003 + idx)
        chosen = tuple(agent.choose(scenario))
        opt = optimal_value(scenario)
        feasible = scenario.is_feasible(chosen)
        achieved = scenario.total_value(chosen) if feasible else 0
        rows.append(
            ScenarioScore(
                scenario_seed=scenario.seed,
                n_items=scenario.n_items,
                budget=scenario.budget,
                optimal_value=opt,
                achieved_value=achieved,
                feasible=feasible,
                score=score_allocation(scenario, chosen, opt),
            )
        )
    feasible_rate = (sum(1 for r in rows if r.feasible) / len(rows)) if rows else 0.0
    return SuiteResult(
        agent_name=getattr(agent, "name", "agent"),
        score=Stat.of([r.score for r in rows]),
        feasible_rate=feasible_rate,
        scenarios=rows,
    )
