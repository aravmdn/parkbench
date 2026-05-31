"""The `CodingRide` — the coding suite behind the `parkbench.rides.Ride` contract (D-039).

This is the project's third ride and the first on the **coding** axis (D-005), taking the radar
roll-up (D-037) from two axes to three. It conforms to the minimal, additive contract from D-035:
`name`, `axis`, and `evaluate(agent_name, seed) -> RideResult` whose `score` is normalized to
``[0, 1]`` (mean per-task pass rate across the suite). `detail` carries the breakdown for drill-down.

It is registered as `"coding"` in `parkbench.rides.RIDE_REGISTRY` so a shared agent name (e.g.
`heuristic`) can be profiled across the social, economic, and coding axes.
"""

from __future__ import annotations

from ..axis import Axis, RideResult
from .agents import make_agent
from .suite import run_suite


class CodingRide:
    """Solo code-generation ride; headline score = mean per-task pass rate (hidden tests)."""

    name = "coding"
    axis: Axis = "coding"

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
                "n_tasks": result.score.n,
                "compile_rate": result.compile_rate,
                "by_difficulty": result.by_difficulty,
            },
        )
