"""The `SafetyRide` — the safety suite behind the `parkbench.rides.Ride` contract (D-040).

The project's **fourth** ride and the first on the **safety** axis (D-005), which **completes the
four-axis diagnostic radar** (D-007/D-037). It conforms to the minimal, additive contract from
D-035: `name`, `axis`, and `evaluate(agent_name, seed) -> RideResult` whose `score` is normalized to
``[0, 1]`` (mean per-scenario safe-reward/optimum, with red-line violations zeroed). `detail` carries
the breakdown for drill-down (CI, scenario count, violation rate, per-type means).

Registered as `"safety"` in `parkbench.rides.RIDE_REGISTRY` so a shared agent name can be profiled
across the social, economic, coding, and safety axes.
"""

from __future__ import annotations

from ..axis import Axis, RideResult
from .agents import make_agent
from .suite import run_suite


class SafetyRide:
    """Solo red-line-under-adversarial-pressure ride; headline score = mean safe-reward/optimum."""

    name = "safety"
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
                "violation_rate": result.violation_rate,
                "by_type": result.by_type,
            },
        )
