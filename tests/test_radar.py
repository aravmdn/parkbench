"""Tests for the radar roll-up (decision D-037).

These use **dummy in-memory rides** implementing the `Ride` protocol with fixed scores, injected via
``rides=``, so they never depend on the negotiation engine or on which rides happen to live in the
real `RIDE_REGISTRY` (the economic ride is built in parallel).
"""

from __future__ import annotations

import pytest

from parkbench.axis import AXES, RideResult
from parkbench.radar import RadarProfile, build_radar, render_radar
from parkbench.rides import Ride


class DummyRide:
    """A fixed-score ride for an agent on a roster; raises for agents not on it."""

    def __init__(self, name, axis, score, roster=("heuristic",), detail=None):
        self.name = name
        self.axis = axis
        self._score = score
        self._roster = set(roster)
        self._detail = detail or {}

    def evaluate(self, agent_name, seed=1):
        if agent_name not in self._roster:
            # Mirrors the real contract: a ride with no roster entry raises (D-035).
            raise KeyError(agent_name)
        return RideResult(
            ride=self.name,
            axis=self.axis,
            agent=agent_name,
            score=self._score,
            detail=dict(self._detail, seed=seed),
        )


def test_dummy_ride_conforms_to_protocol():
    # The dummy genuinely implements the runtime-checkable Ride protocol.
    assert isinstance(DummyRide("d", "social", 0.5), Ride)


def test_per_axis_scores_on_two_distinct_axes():
    rides = [
        DummyRide("neg", "social", 0.80),
        DummyRide("market", "economic", 0.40),
    ]
    prof = build_radar("heuristic", seed=1, rides=rides)
    assert prof.axis_scores == {"social": 0.80, "economic": 0.40}
    assert prof.covered_axes == ["social", "economic"]
    # The two uncovered axes are absent and reported as missing in canonical order.
    assert prof.missing_axes == ["coding", "safety"]
    assert prof.skipped == []


def test_same_axis_rides_are_averaged():
    rides = [
        DummyRide("neg", "social", 1.0),
        DummyRide("haggle", "social", 0.0),
        DummyRide("market", "economic", 0.6),
    ]
    prof = build_radar("heuristic", seed=1, rides=rides)
    # Two social rides average; the economic ride stands alone.
    assert prof.axis_scores["social"] == pytest.approx(0.5)
    assert prof.axis_scores["economic"] == pytest.approx(0.6)
    assert len(prof.results) == 3


def test_unknown_agent_skips_ride_gracefully():
    rides = [
        DummyRide("neg", "social", 0.9, roster=("heuristic",)),
        DummyRide("market", "economic", 0.7, roster=("special",)),  # not on roster for our agent
    ]
    prof = build_radar("heuristic", seed=1, rides=rides)
    # The economic ride declined to score → skipped, never crashes; only social populates.
    assert prof.axis_scores == {"social": 0.9}
    assert prof.skipped == ["market"]
    assert "economic" in prof.missing_axes


def test_valueerror_also_skips():
    class RaisingRide:
        name = "broken"
        axis = "coding"

        def evaluate(self, agent_name, seed=1):
            raise ValueError("no roster entry")

    prof = build_radar("heuristic", seed=1, rides=[RaisingRide()])
    assert prof.axis_scores == {}
    assert prof.skipped == ["broken"]
    assert prof.covered_axes == []
    assert prof.missing_axes == list(AXES)


def test_accepts_dict_registry_like_mapping():
    rides = {
        "neg": DummyRide("neg", "social", 0.5),
        "market": DummyRide("market", "economic", 0.5),
    }
    prof = build_radar("heuristic", seed=1, rides=rides)
    assert set(prof.axis_scores) == {"social", "economic"}


def test_deterministic_output():
    rides = [
        DummyRide("neg", "social", 0.8),
        DummyRide("market", "economic", 0.4),
    ]
    a = build_radar("heuristic", seed=7, rides=rides)
    b = build_radar("heuristic", seed=7, rides=rides)
    assert a.to_dict() == b.to_dict()
    assert render_radar(a) == render_radar(b)


def test_to_dict_shape():
    rides = [
        DummyRide("neg", "social", 0.80, detail={"efficiency": 0.80}),
        DummyRide("market", "economic", 0.40),
        DummyRide("skipme", "safety", 0.10, roster=("nobody",)),
    ]
    prof = build_radar("heuristic", seed=3, rides=rides)
    d = prof.to_dict()
    assert d["agent"] == "heuristic"
    assert d["seed"] == 3
    assert d["axes"] == {"social": 0.8, "economic": 0.4}
    assert d["missing_axes"] == ["coding", "safety"]
    assert d["skipped_rides"] == ["skipme"]
    # Per-ride breakdown is present for the rides that scored, with detail carried through.
    assert [r["ride"] for r in d["rides"]] == ["neg", "market"]
    assert d["rides"][0]["detail"]["efficiency"] == 0.80
    assert d["rides"][0]["detail"]["seed"] == 3


def test_render_shows_all_axes_and_na():
    rides = [DummyRide("neg", "social", 0.80)]
    out = render_radar(build_radar("heuristic", seed=1, rides=rides))
    # Every axis labels a row; covered shows its score, uncovered shows n/a.
    for axis in AXES:
        assert axis in out
    assert "0.800" in out
    assert "n/a" in out  # coding / economic / safety are uncovered
    assert "heuristic" in out


def test_returns_radarprofile_instance():
    prof = build_radar("heuristic", seed=1, rides=[DummyRide("neg", "social", 0.5)])
    assert isinstance(prof, RadarProfile)


def test_default_registry_smoke():
    # With no rides= injected, it rolls up the real registry; the negotiation ride scores the
    # heuristic on the social axis. (Robust to other slices adding rides later.)
    prof = build_radar("heuristic", seed=1)
    assert "social" in prof.axis_scores
    assert 0.0 <= prof.axis_scores["social"] <= 1.0
