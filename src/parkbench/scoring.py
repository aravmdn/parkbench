"""Objective payoff scoring (decision D-019).

Two metrics per match, both in [0, 1] and 0 on no-deal:
  - efficiency  = (uA + uB) / max_joint   -> "joint value captured": did they find the
                  value-creating trades? (1.0 == on the welfare-maximizing frontier)
  - own_value   = uA / max_a              -> "own share": how much the test agent (party A)
                  captured for itself, relative to its best possible agreement.

Aggregation reports mean, sample std, and a 95% confidence interval. The CI/variance is
the evidence for the v1 reproducibility claim (decision D-020).
"""

from __future__ import annotations

import math
import statistics
from dataclasses import dataclass

from .engine import MatchResult
from .scenario import Analysis, Scenario


@dataclass
class MatchScore:
    persona: str
    scenario_seed: int | None
    agreed: bool
    efficiency: float
    own_value: float
    off_record: bool = False  # nudged matches (D-029); excluded from canonical aggregation


def score_match(
    scenario: Scenario,
    analysis: Analysis,
    result: MatchResult,
    persona_name: str,
    off_record: bool = False,
) -> MatchScore:
    if not result.agreed or result.outcome is None:
        return MatchScore(persona_name, scenario.seed, False, 0.0, 0.0, off_record)
    levels = result.outcome.levels
    ua = scenario.util_a(levels)
    ub = scenario.util_b(levels)
    efficiency = (ua + ub) / analysis.max_joint if analysis.max_joint > 0 else 0.0
    own_value = ua / analysis.max_a if analysis.max_a > 0 else 0.0
    return MatchScore(persona_name, scenario.seed, True, efficiency, own_value, off_record)


@dataclass
class Stat:
    mean: float
    std: float
    ci95: float
    n: int

    @classmethod
    def of(cls, values) -> "Stat":
        vals = list(values)
        n = len(vals)
        if n == 0:
            return cls(0.0, 0.0, 0.0, 0)
        std = statistics.stdev(vals) if n > 1 else 0.0
        ci95 = 1.96 * std / math.sqrt(n) if n > 1 else 0.0
        return cls(statistics.fmean(vals), std, ci95, n)


@dataclass
class Profile:
    agent_name: str
    efficiency: Stat
    own_value: Stat
    deal_rate: float
    per_persona: dict  # persona -> {"efficiency": Stat, "own_value": Stat, "deal_rate": float}
    matches: list  # list[MatchScore] — the matches that fed the canonical aggregation
    off_record: bool = False  # True when this profile is built from nudged matches (D-029)
    excluded: int = 0  # count of off-record matches dropped from canonical aggregation


def build_profile(agent_name: str, matches: list[MatchScore]) -> Profile:
    """Aggregate match scores into a canonical (on-record) profile.

    Off-record matches (nudged runs — D-029) are EXCLUDED from the canonical aggregation
    so they cannot pollute the scores; only their count is retained (`excluded`). To build
    a profile *of* nudged matches instead, use `build_off_record_profile`.
    """
    on_record = [m for m in matches if not m.off_record]
    excluded = len(matches) - len(on_record)
    profile = _aggregate(agent_name, on_record)
    profile.excluded = excluded
    return profile


def build_off_record_profile(agent_name: str, matches: list[MatchScore]) -> Profile:
    """Aggregate nudged matches into a clearly-flagged off-record profile (D-029).

    Never feeds canonical scores; produced only for the observe+nudge replay surface.
    """
    profile = _aggregate(agent_name, list(matches))
    profile.off_record = True
    return profile


def _aggregate(agent_name: str, matches: list[MatchScore]) -> Profile:
    deal_rate = (sum(1 for m in matches if m.agreed) / len(matches)) if matches else 0.0
    per_persona: dict = {}
    for p in sorted({m.persona for m in matches}):
        group = [m for m in matches if m.persona == p]
        per_persona[p] = {
            "efficiency": Stat.of([m.efficiency for m in group]),
            "own_value": Stat.of([m.own_value for m in group]),
            "deal_rate": sum(1 for m in group if m.agreed) / len(group),
        }
    return Profile(
        agent_name,
        Stat.of([m.efficiency for m in matches]),
        Stat.of([m.own_value for m in matches]),
        deal_rate,
        per_persona,
        list(matches),
    )
