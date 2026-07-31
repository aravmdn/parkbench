"""The `ContainmentRide` — the containment suite behind the `parkbench.rides.Ride` contract (D-071).

The project's **seventh** ride and the **second on the safety axis** (D-005), so the safety axis
joins social (D-045) and economic (D-066) in being a per-axis **mean of two rides** (D-037) — and
gains its first within-axis (monotrait) pair for the MTMM discriminant matrix (D-057). It conforms
to the minimal, additive contract from D-035: `name`, `axis`, and
`evaluate(agent_name, seed) -> RideResult` whose `score` is normalized to ``[0, 1]`` (mean
breach-free-bracketed output, with envelope breaches zeroed).

Registered as `"containment"` in `parkbench.rides.RIDE_REGISTRY`.
"""

from __future__ import annotations

from ..axis import Axis, RideResult
from .agents import make_agent
from .suite import run_suite


class ContainmentRide:
    """Solo safety-envelope ride; headline score = mean breach-free-bracketed output."""

    name = "containment"
    axis: Axis = "safety"

    def evaluate(self, agent_name: str, seed: int = 1) -> RideResult:
        result = run_suite(make_agent(agent_name), seed=seed)
        return RideResult(
            ride=self.name,
            axis=self.axis,
            agent=agent_name,
            score=result.score.mean,
            detail={
                "score": result.score.mean,
                "ci95": result.score.ci95,
                "std": result.score.std,
                "n_scenarios": result.score.n,
                "breach_rate": result.breach_rate,
                "by_type": result.by_type,
                # Cross-ride integrity signal for the career roll-up (D-041). This ride HAS a hard
                # rule the agent can violate — the declared safety envelope — so, unlike the neutral
                # 1.0 of negotiation/commons/exchange, conduct is the non-breach rate. It is the
                # exact analogue of the economic ride's `feasible_rate` ("stayed inside a declared
                # hard constraint") and of the red-line ride's `1 - violation_rate`.
                "integrity": 1.0 - result.breach_rate,
            },
        )
