"""The `CommonsRide` — the public-goods suite behind the `parkbench.rides.Ride` contract (D-045).

This is the project's **fifth** ride and the **second on the social axis** (D-005), so it is the
first ride to *share an axis* with another (the negotiation ride) — exercising the radar roll-up's
per-axis **mean** (D-037) for the first time with real rides. It conforms to the minimal, additive
contract from D-035: `name`, `axis`, and `evaluate(agent_name, seed) -> RideResult` whose `score` is
normalized to `[0, 1]` (mean best/worst-response-normalized payoff across the suite).

Registered as `"commons"` in `parkbench.rides.RIDE_REGISTRY`.
"""

from __future__ import annotations

from ..axis import Axis, RideResult
from .agents import make_agent
from .suite import run_suite


class CommonsRide:
    """Multi-agent public-goods (cooperation) ride; headline score = mean response-normalized payoff."""

    name = "commons"
    axis: Axis = "social"

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
                "cooperation_rate": result.cooperation_rate,
                # Cross-ride integrity signal for the career roll-up (D-041): like the negotiation
                # ride, the commons ride has no hard rule to *violate* — free-riding is a legitimate
                # (if poorly-rewarded) strategy, and its cost is already priced into the score, so it
                # must not be double-counted as misconduct. Conduct here is neutral — 1.0.
                "integrity": 1.0,
            },
        )
