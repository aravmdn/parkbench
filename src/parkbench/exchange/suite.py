"""The fixed exchange-ride suite + per-scenario bracket scoring (decision D-066).

Scoring is a **best/worst-response bracket** (borrowed from the commons ride, D-045 — *not* the
knapsack's ``achieved/optimal``, D-036):

    score = (achieved - worst) / (optimal - worst)   clamped to [0, 1]

where ``optimal`` / ``worst`` are the exact max- / min-weight matchings of the surplus matrix. This
is a deliberate choice to attack the knapsack ride's flagged weakness (a high 0.71 random floor,
docs/12-validity.md): normalizing against the genuinely-*worst* matching (not 0) spreads the baselines
and gives `random` a materially lower floor, so the economic axis gets a wide dynamic range. The
``optimal`` matching scores 1.0 by construction and the ``worst`` matching scores 0.0. A malformed
(non-permutation) choice scores 0. If the bracket is degenerate (``optimal == worst`` — no allocative
variation), any assignment is optimal ⇒ 1.0.

A *score* over the ride is the mean of the per-scenario scores across a fixed suite of ~12 seeded
instances, reported with a 95% CI (reusing `scoring.Stat`, exactly as every other ride does, so the
variance — the reproducibility evidence — is reported the same way across rides). Alongside the
headline we report the mean **surplus efficiency** (``achieved / optimal``) as a behavioral diagnostic.
Everything is seed-derived: same suite seed ⇒ identical instances ⇒ identical scores.
"""

from __future__ import annotations

from dataclasses import dataclass

from ..scoring import Stat
from .agents import ExchangeAgent
from .scenario import ExchangeScenario, generate_scenario, solve_optimum, solve_worst

DEFAULT_N_SCENARIOS = 12


def score_assignment(
    scenario: ExchangeScenario,
    assignment,
    optimum: int | None = None,
    worst: int | None = None,
) -> float:
    """Score one assignment on the best/worst-response bracket, clamped to [0, 1]; 0 if malformed.

    ``(achieved - worst) / (optimal - worst)``. A non-permutation choice scores 0 (there is no
    partial credit for an invalid allocation). A degenerate bracket (optimal == worst) scores 1.0.
    """
    if not scenario.is_valid(assignment):
        return 0.0
    opt = solve_optimum(scenario)[0] if optimum is None else optimum
    wrst = solve_worst(scenario)[0] if worst is None else worst
    spread = opt - wrst
    if spread <= 0:
        return 1.0
    achieved = scenario.total_surplus(assignment)
    return max(0.0, min(1.0, (achieved - wrst) / spread))


@dataclass
class ScenarioScore:
    scenario_seed: int | None
    n_traders: int
    worst: int
    optimal: int
    achieved: int
    valid: bool
    efficiency: float  # achieved / optimal, in [0, 1] — a behavioral diagnostic
    score: float


@dataclass
class SuiteResult:
    agent_name: str
    score: Stat  # mean +/- 95% CI of per-scenario bracket scores
    efficiency_rate: float  # mean achieved/optimal across the suite
    scenarios: list  # list[ScenarioScore] — the per-scenario breakdown


def build_scenarios(seed: int, n_scenarios: int = DEFAULT_N_SCENARIOS) -> list[ExchangeScenario]:
    """The fixed suite: `n_scenarios` instances derived deterministically from the suite seed."""
    return [generate_scenario(seed + s) for s in range(n_scenarios)]


def run_suite(
    agent: ExchangeAgent, seed: int = 1, n_scenarios: int = DEFAULT_N_SCENARIOS
) -> SuiteResult:
    """Run an exchange agent through the fixed suite and aggregate its profile.

    Each scenario re-seeds the agent deterministically (so the `random` baseline is reproducible)
    before asking it to `choose`. The best/worst matchings are solved once per scenario and shared
    with scoring.
    """
    scenarios = build_scenarios(seed, n_scenarios)
    rows: list[ScenarioScore] = []
    for idx, scenario in enumerate(scenarios):
        agent.reset(seed=seed * 1_000_003 + idx)
        assignment = tuple(agent.choose(scenario))
        opt = solve_optimum(scenario)[0]
        wrst = solve_worst(scenario)[0]
        valid = scenario.is_valid(assignment)
        achieved = scenario.total_surplus(assignment) if valid else 0
        efficiency = (achieved / opt) if (valid and opt > 0) else 0.0
        rows.append(
            ScenarioScore(
                scenario_seed=scenario.seed,
                n_traders=scenario.n,
                worst=wrst,
                optimal=opt,
                achieved=achieved,
                valid=valid,
                efficiency=efficiency,
                score=score_assignment(scenario, assignment, opt, wrst),
            )
        )
    efficiency_rate = (sum(r.efficiency for r in rows) / len(rows)) if rows else 0.0
    return SuiteResult(
        agent_name=getattr(agent, "name", "agent"),
        score=Stat.of([r.score for r in rows]),
        efficiency_rate=efficiency_rate,
        scenarios=rows,
    )
