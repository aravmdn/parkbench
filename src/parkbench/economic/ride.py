"""The `EconomicRide` — the knapsack suite behind the `parkbench.rides.Ride` contract (D-036).

This is the second ride and the first on the **economic** axis (D-005), giving the radar roll-up
(D-037) a second axis to plot. The ride conforms to the minimal, additive contract from D-035:
`name`, `axis`, and `evaluate(agent_name, seed) -> RideResult` whose `score` is normalized to
`[0, 1]` (mean achieved/optimal across the suite). `detail` carries the breakdown for drill-down.

It is registered as `"economic"` in `parkbench.rides.RIDE_REGISTRY` so a shared agent name (e.g.
`greedy`) can be profiled across both the social and economic axes.
"""

from __future__ import annotations

from ..axis import Axis, RideResult
from .agents import make_agent
from .suite import run_suite


class EconomicRide:
    """Solo resource-allocation (0/1 knapsack) ride; headline score = mean achieved/optimal."""

    name = "economic"
    axis: Axis = "economic"

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
                "feasible_rate": result.feasible_rate,
                # Cross-ride integrity signal for the career roll-up (D-041): staying within the
                # budget is the ride's hard constraint, so feasibility *is* rule-compliance — an
                # infeasible (over-budget) allocation is a constraint breach that costs reputation.
                "integrity": result.feasible_rate,
            },
        )
