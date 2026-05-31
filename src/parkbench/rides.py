"""The ride abstraction + registry (decision D-035).

A *ride* is a self-contained, scored capability test (D-002). Each one exposes its `name`, its
`axis` (D-005), and an `evaluate(agent_name, seed) -> RideResult` that returns a normalized headline
score plus a ride-specific detail blob. Rides stay independent (D-008); the radar roll-up (D-037)
combines their results into the diagnostic profile (D-007).

This module is **purely additive** — it adapts the existing negotiation suite rather than changing
it — so the original `parkbench run` path is untouched. New rides register themselves in
`RIDE_REGISTRY`.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from .agents import make_agent
from .axis import Axis, RideResult
from .coding import CodingRide  # D-039: registers the coding (code-generation) ride below
from .economic import EconomicRide  # D-036: registers the economic (knapsack) ride below
from .safety import SafetyRide  # D-040: registers the safety (red-line) ride below
from .suite import Suite, run_suite


@runtime_checkable
class Ride(Protocol):
    name: str
    axis: Axis

    def evaluate(self, agent_name: str, seed: int = 1) -> RideResult: ...


class NegotiationRide:
    """The v1 flagship ride, wrapped behind the `Ride` contract (D-010, D-035).

    Its normalized headline `score` is the mean **efficiency** (joint value captured vs. the
    game-theoretic optimum), already in `[0, 1]`; `own_value`/`deal_rate` ride along in `detail`.
    """

    name = "negotiation"
    axis: Axis = "social"

    def evaluate(self, agent_name: str, seed: int = 1) -> RideResult:
        profile, _records = run_suite(Suite(seed=seed), make_agent(agent_name))
        return RideResult(
            ride=self.name,
            axis=self.axis,
            agent=agent_name,
            score=profile.efficiency.mean,
            detail={
                "efficiency": profile.efficiency.mean,
                "own_value": profile.own_value.mean,
                "deal_rate": profile.deal_rate,
            },
        )


# Rides available for radar roll-up. New rides add themselves here.
RIDE_REGISTRY: dict[str, Ride] = {
    "negotiation": NegotiationRide(),
    "economic": EconomicRide(),  # D-036: solo resource-allocation (knapsack) ride
    "coding": CodingRide(),  # D-039: solo code-generation ride (hidden-test scored)
    "safety": SafetyRide(),  # D-040: solo red-line-under-adversarial-pressure ride
}
