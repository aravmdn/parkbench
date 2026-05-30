"""The fixed v1 scenario suite and the runner that produces an agent's profile.

A `Suite` is fully defined by its seed + counts, so it regenerates identically every time
(decision D-020). The runner plays the test agent against every house persona on every
scenario, seeding both agents deterministically per match so whole runs are reproducible.

A run may also be *nudged* (decision D-029): a human can swap the counterpart persona or
inject a chosen scenario. Nudged runs are flagged off-record and excluded from canonical
profiles — see `parkbench.nudge` and `parkbench.scoring`.
"""

from __future__ import annotations

from dataclasses import dataclass

from .agents.base import Agent
from .engine import run_match
from .nudge import Nudge
from .scenario import Scenario, analyze, generate_scenario, shape_for_index
from .scoring import Profile, build_off_record_profile, build_profile, score_match


@dataclass(frozen=True)
class Suite:
    name: str = "v1_negotiation"
    seed: int = 1
    n_scenarios: int = 12
    n_issues: int = 4  # fallback shape when vary_shapes is off
    n_levels: int = 3
    round_cap: int = 8
    vary_shapes: bool = True  # cycle issue/level counts across scenarios (decision D-032)

    def shape(self, index: int) -> tuple[int, int]:
        """The (n_issues, n_levels) for scenario `index` in this suite."""
        if self.vary_shapes:
            return shape_for_index(index)
        return self.n_issues, self.n_levels


def run_suite(
    suite: Suite, agent: Agent, nudge: Nudge | None = None
) -> tuple[Profile, list[dict]]:
    """Run an agent through the suite, optionally under a nudge.

    Without a nudge this is the canonical, on-record path (unchanged behaviour). With a
    nudge — persona swap and/or scenario injection — every match is flagged off-record and
    the resulting profile is built off-record so it never pollutes canonical aggregation.
    """
    nudge = nudge or Nudge()
    off_record = nudge.off_record
    roster = nudge.roster()

    if nudge.inject_scenario is not None:
        scenarios: list[Scenario] = [nudge.inject_scenario]
    else:
        scenarios = [
            generate_scenario(suite.seed + s, *suite.shape(s))
            for s in range(suite.n_scenarios)
        ]

    matches = []
    records: list[dict] = []
    for s, scenario in enumerate(scenarios):
        analysis = analyze(scenario)
        for p_idx, persona_cls in enumerate(roster):
            persona = persona_cls()
            match_seed = suite.seed * 1_000_003 + s * 101 + p_idx
            agent.reset(seed=match_seed, total_rounds=suite.round_cap)
            persona.reset(seed=match_seed + 7, total_rounds=suite.round_cap)
            result = run_match(scenario, agent, persona, suite.round_cap)
            score = score_match(scenario, analysis, result, persona.name, off_record)
            matches.append(score)
            records.append(
                {
                    "scenario_seed": scenario.seed,
                    "n_issues": scenario.n_issues,
                    "n_levels": scenario.n_levels,
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
                    # Added by D-029; placed last so existing fields/positions are unchanged.
                    "off_record": off_record,
                }
            )
    builder = build_off_record_profile if off_record else build_profile
    return builder(agent.name, matches), records
