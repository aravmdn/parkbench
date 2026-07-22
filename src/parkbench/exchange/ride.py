"""The `ExchangeRide` — the assignment suite behind the `parkbench.rides.Ride` contract (D-066).

This is the project's **sixth** ride and the **second on the economic axis** (D-005), so it is the
first ride to *share the economic axis* with another (the knapsack ride, D-036) — making the radar's
per-axis **mean** (D-037) the economic axis' aggregation, exactly as the commons ride did for the
social axis. It conforms to the minimal, additive contract from D-035: `name`, `axis`, and
`evaluate(agent_name, seed) -> RideResult` whose `score` is normalized to `[0, 1]` (mean
best/worst-response-bracketed surplus across the suite).

Registered as `"exchange"` in `parkbench.rides.RIDE_REGISTRY`.
"""

from __future__ import annotations

from ..axis import Axis, RideResult
from .agents import make_agent
from .suite import run_suite


class ExchangeRide:
    """Solo allocative-efficiency (assignment) ride; headline score = mean response-bracketed surplus."""

    name = "exchange"
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
                "efficiency_rate": result.efficiency_rate,
                # Cross-ride integrity signal for the career roll-up (D-041): like the commons and
                # negotiation rides, the exchange ride has no hard rule to *violate* — every
                # permutation is a legitimate allocation, and a poor matching already costs surplus
                # (priced into the score), so conduct is neutral. Keeping it neutral also keeps the
                # ride's discriminating signal purely allocative, so it converges with the *economic*
                # axis rather than smuggling in a red-line signal (docs/13 §A.2). Conduct = 1.0.
                "integrity": 1.0,
            },
        )
