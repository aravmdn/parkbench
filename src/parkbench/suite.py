"""The fixed v1 scenario suite and the runner that produces an agent's profile.

A `Suite` is fully defined by its seed + counts, so it regenerates identically every time
(decision D-020). The runner plays the test agent against every house persona on every
scenario, seeding both agents deterministically per match so whole runs are reproducible.
"""

from __future__ import annotations

from dataclasses import dataclass

from .agents.base import Agent
from .engine import run_match
from .personas import HOUSE_CAST
from .scenario import analyze, generate_scenario
from .scoring import Profile, build_profile, score_match


@dataclass(frozen=True)
class Suite:
    name: str = "v1_negotiation"
    seed: int = 1
    n_scenarios: int = 12
    n_issues: int = 4
    n_levels: int = 3
    round_cap: int = 8


def run_suite(suite: Suite, agent: Agent) -> tuple[Profile, list[dict]]:
    matches = []
    records: list[dict] = []
    for s in range(suite.n_scenarios):
        scenario = generate_scenario(suite.seed + s, suite.n_issues, suite.n_levels)
        analysis = analyze(scenario)
        for p_idx, persona_cls in enumerate(HOUSE_CAST):
            persona = persona_cls()
            match_seed = suite.seed * 1_000_003 + s * 101 + p_idx
            agent.reset(seed=match_seed, total_rounds=suite.round_cap)
            persona.reset(seed=match_seed + 7, total_rounds=suite.round_cap)
            result = run_match(scenario, agent, persona, suite.round_cap)
            score = score_match(scenario, analysis, result, persona.name)
            matches.append(score)
            records.append(
                {
                    "scenario_seed": scenario.seed,
                    "persona": persona.name,
                    "agreed": result.agreed,
                    "outcome": result.outcome.to_dict() if result.outcome else None,
                    "efficiency": score.efficiency,
                    "own_value": score.own_value,
                    "turns_used": result.turns_used,
                    "transcript": result.transcript,
                    "analysis": {
                        "max_joint": analysis.max_joint,
                        "max_a": analysis.max_a,
                        "max_b": analysis.max_b,
                        "nash_outcome": list(analysis.nash_outcome),
                    },
                }
            )
    return build_profile(agent.name, matches), records
