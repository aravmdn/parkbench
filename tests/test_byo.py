"""The live BYO connector (chunk-4 ``byo-live-connector``).

The central claim: a BYO agent driven over the **real** ``docs/09`` HTTP wire produces the same
negotiation result the in-process :class:`~parkbench.rides.NegotiationRide` produces — so the world's
BYO trainer can be fed live protocol traffic instead of a hand-authored fixture without inventing a
second scoring path (D-012). The second claim is honesty: the wire scores exactly one ride, so the
captured profile covers exactly one axis and says so.

Everything runs in-process on an ephemeral loopback port (``port=0``); no external network.
"""

from __future__ import annotations

import json

from parkbench import BENCHMARK_VERSION, cli
from parkbench.agents import make_agent
from parkbench.byo import (
    DEFAULT_BYO_NAME,
    ByoRun,
    render_byo_run,
    run_byo_from_name,
    run_byo_negotiation,
)
from parkbench.radar import build_radar
from parkbench.rides import RIDE_REGISTRY, NegotiationRide

# One suite run per call crosses a socket ~190 times, so the shared fixtures below are built once
# per module rather than per test (a plain module-level cache keeps this dependency-free).
_CACHE: dict[tuple, ByoRun] = {}


def _run(agent_name: str = "heuristic", seed: int = 1, **kwargs) -> ByoRun:
    key = (agent_name, seed, tuple(sorted(kwargs.items())))
    if key not in _CACHE:
        _CACHE[key] = run_byo_from_name(agent_name, seed=seed, **kwargs)
    return _CACHE[key]


# --- the wire reproduces the in-process ride ----------------------------------------------


def test_wired_run_matches_the_in_process_negotiation_ride():
    """A run over the socket == the same agent's in-process ride result, detail for detail.

    This is the load-bearing test: it is what makes a live BYO profile comparable to a baseline's,
    and it proves the connector transports rather than re-scores.
    """
    wired = _run("heuristic", seed=1)
    in_process = NegotiationRide().evaluate("heuristic", 1)

    leg = wired.profile.results[0]
    assert leg.score == in_process.score
    assert leg.detail == in_process.detail
    assert leg.ride == "negotiation"
    assert leg.axis == "social"


def test_wired_run_matches_the_in_process_ride_for_a_seed_dependent_agent():
    """`random` re-seeds per match, so parity here proves the `new_match` re-seed hop works."""
    wired = _run("random", seed=3)
    assert wired.profile.results[0].score == NegotiationRide().evaluate("random", 3).score


def test_payload_is_deterministic():
    """Same agent + same seed => byte-identical JSON. No clock, no port, no run-to-run drift."""
    first = run_byo_from_name("heuristic", seed=2).to_dict()
    second = run_byo_from_name("heuristic", seed=2).to_dict()
    assert json.dumps(first, sort_keys=True) == json.dumps(second, sort_keys=True)
    payload = json.dumps(first)
    assert "captured_at" not in payload and "timestamp" not in payload
    # The ephemeral port is run mechanics, never run results.
    assert "port" not in payload


# --- the profile is honest about what the wire could measure -------------------------------


def test_profile_covers_only_the_social_axis():
    """The v1 wire carries negotiation only, so exactly one axis is covered and three are missing."""
    run = _run("heuristic", seed=1)
    assert run.profile.covered_axes == ["social"]
    assert run.profile.missing_axes == ["economic", "coding", "safety"]
    payload = run.to_dict()
    assert set(payload["axes"]) == {"social"}
    assert payload["missing_axes"] == ["economic", "coding", "safety"]


def test_every_other_registered_ride_is_reported_skipped():
    """Rides the wire cannot reach are named, not silently dropped — and the list tracks the registry."""
    run = _run("heuristic", seed=1)
    expected = [name for name in RIDE_REGISTRY if name != "negotiation"]
    assert run.profile.skipped == expected
    assert run.to_dict()["skipped_rides"] == expected

