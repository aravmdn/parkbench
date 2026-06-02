"""The fixed commons-ride suite + aggregation (decision D-045).

Scoring is the per-scenario `score_total` (achieved total payoff normalized onto ``[0, 1]`` against
the exact best/worst-response bracket against the fixed cast). A *score* over the ride is the **mean
per-scenario score** across a fixed suite of seeded games, reported with a 95% CI via the shared
`scoring.Stat` — the same way variance (the reproducibility evidence) is reported across every ride.

Alongside the headline score we report a **cooperation rate** (A's mean contribution as a fraction of
its endowment) — a behavioral diagnostic that separates the free-rider (≈0) from the cooperators —
and the mean achieved payoff. Everything is seed-derived: same suite seed ⇒ identical games ⇒
identical scores.
"""

from __future__ import annotations

from dataclasses import dataclass

from ..scoring import Stat
from .agents import CommonsAgent
from .scenario import (
    CommonsScenario,
    generate_scenario,
    simulate,
    solve_response_bounds,
    score_total,
)

DEFAULT_N_SCENARIOS = 12


def _agent_policy(agent: CommonsAgent, scenario: CommonsScenario):
    """Adapt a `CommonsAgent` to the simulator's ``(round_idx, history) -> contribution`` policy."""
    return lambda r, history: agent.contribute(r, history, scenario)


@dataclass
class ScenarioScore:
    scenario_seed: int | None
    n_rounds: int
    endowment: int
    multiplier: float
    best: float
    worst: float
    achieved: float
    cooperation: float  # A's mean contribution / endowment, in [0, 1]
    score: float


@dataclass
class SuiteResult:
    agent_name: str
    score: Stat  # mean ± 95% CI of per-scenario normalized score
    cooperation_rate: float  # mean A contribution / endowment across the suite
    scenarios: list  # list[ScenarioScore]


def build_scenarios(seed: int, n_scenarios: int = DEFAULT_N_SCENARIOS) -> list[CommonsScenario]:
    """The fixed suite: `n_scenarios` games derived deterministically from the suite seed."""
    return [generate_scenario(seed + s) for s in range(n_scenarios)]


def run_suite(
    agent: CommonsAgent, seed: int = 1, n_scenarios: int = DEFAULT_N_SCENARIOS
) -> SuiteResult:
    """Run a commons agent through the fixed suite and aggregate its profile.

    Each game re-seeds the agent deterministically (so the `random` baseline is reproducible) before
    play. The best/worst-response bracket is solved once per game and shared with scoring.
    """
    scenarios = build_scenarios(seed, n_scenarios)
    rows: list[ScenarioScore] = []
    for idx, scenario in enumerate(scenarios):
        agent.reset(seed=seed * 1_000_003 + idx)
        achieved, detail = simulate(scenario, _agent_policy(agent, scenario))
        bounds = solve_response_bounds(scenario)
        a_contribs = [d.contributions[0] for d in detail]
        cooperation = (
            (sum(a_contribs) / len(a_contribs)) / scenario.endowment if a_contribs else 0.0
        )
        rows.append(
            ScenarioScore(
                scenario_seed=scenario.seed,
                n_rounds=scenario.n_rounds,
                endowment=scenario.endowment,
                multiplier=scenario.multiplier,
                best=bounds.best,
                worst=bounds.worst,
                achieved=achieved,
                cooperation=cooperation,
                score=score_total(scenario, achieved, bounds),
            )
        )
    cooperation_rate = (sum(r.cooperation for r in rows) / len(rows)) if rows else 0.0
    return SuiteResult(
        agent_name=getattr(agent, "name", "agent"),
        score=Stat.of([r.score for r in rows]),
        cooperation_rate=cooperation_rate,
        scenarios=rows,
    )
