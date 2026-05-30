"""Tests for the ride abstraction + registry (D-035)."""

from __future__ import annotations

from parkbench.axis import AXES, RideResult
from parkbench.rides import RIDE_REGISTRY, Ride


def test_negotiation_registered_and_conforms():
    ride = RIDE_REGISTRY["negotiation"]
    assert isinstance(ride, Ride)  # runtime_checkable Protocol
    assert ride.axis == "social"


def test_evaluate_returns_normalized_result():
    r = RIDE_REGISTRY["negotiation"].evaluate("heuristic", seed=1)
    assert isinstance(r, RideResult)
    assert r.axis in AXES
    assert 0.0 <= r.score <= 1.0
    assert r.score > 0.9  # the heuristic captures most of the joint value


def test_evaluate_is_deterministic():
    ride = RIDE_REGISTRY["negotiation"]
    assert ride.evaluate("heuristic", seed=1).score == ride.evaluate("heuristic", seed=1).score
