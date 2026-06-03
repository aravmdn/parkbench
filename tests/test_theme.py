"""Tests for the park skin (decision D-046).

The skin is presentation-only, so these tests pin the two things that actually matter: the skin stays
in **sync with the mechanics** (every registered ride has a themed attraction, every axis a land) and
the rendered map is **terminal-safe and deterministic** (ASCII only — the rest of the CLI is ASCII for
exactly this reason — and identical across calls).
"""

from __future__ import annotations

from parkbench.axis import AXES
from parkbench.rides import RIDE_REGISTRY
from parkbench.theme import (
    ATTRACTIONS,
    LANDS,
    attraction_for,
    render_park_map,
)


def test_every_registered_ride_has_an_attraction():
    # The coverage invariant: a new ride can't ship un-themed (the skin tracks the registry).
    for name in RIDE_REGISTRY:
        assert name in ATTRACTIONS, f"ride '{name}' has no themed attraction"
        assert attraction_for(name).marquee  # non-empty marquee


def test_every_axis_has_a_land():
    for axis in AXES:
        assert axis in LANDS
        assert LANDS[axis].name


def test_attraction_for_unknown_ride_falls_back_without_crashing():
    att = attraction_for("nonexistent-ride")
    assert att.ride == "nonexistent-ride"
    assert att.marquee  # a usable fallback so render never crashes on a fresh ride


def test_map_lists_every_land_attraction_and_command():
    out = render_park_map()
    for axis in AXES:
        assert LANDS[axis].name in out
    for name in RIDE_REGISTRY:
        assert ATTRACTIONS[name].marquee in out
        assert f"parkbench {name} --agent" in out  # how to ride each attraction


def test_map_is_ascii_only_for_terminal_safety():
    out = render_park_map()
    # The CLI is ASCII throughout (e.g. uses "+/-" not "±") so it renders on any console.
    assert out.isascii(), "park map must be ASCII-only for terminal portability"


def test_map_is_deterministic():
    assert render_park_map() == render_park_map()


def test_map_respects_registry_order_within_a_land():
    # Both social rides appear, with negotiation before commons (their registry order).
    out = render_park_map()
    assert out.index(ATTRACTIONS["negotiation"].marquee) < out.index(ATTRACTIONS["commons"].marquee)
