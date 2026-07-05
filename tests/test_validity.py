"""Tests for the validity harness (D-055).

These assert the *harness itself* is correct (its statistics), and that it delivers the two
verdicts it exists to deliver: each fast ride **discriminates known ability**, and the reward-hacker
is **caught**. Configs are kept small (few rungs/seeds) so the suite stays quick; the CLI uses larger
defaults for a tighter read.
"""

from __future__ import annotations

import math

from parkbench import validity as V


# --- pure statistics (instant, no ride runs) -----------------------------------------------------


def test_spearman_and_kendall_perfect_monotone():
    xs = [0.0, 0.2, 0.4, 0.6, 0.8, 1.0]
    ys = [0.0, 0.1, 0.3, 0.35, 0.7, 0.99]  # strictly increasing, non-linear
    assert V.spearman(xs, ys) == 1.0
    assert V.kendall_tau(xs, ys) == 1.0


def test_spearman_and_kendall_perfect_inverse():
    xs = [1, 2, 3, 4]
    ys = [4, 3, 2, 1]
    assert V.spearman(xs, ys) == -1.0
    assert V.kendall_tau(xs, ys) == -1.0


def test_pearson_constant_is_zero():
    assert V.pearson([1, 1, 1], [1, 2, 3]) == 0.0


def test_monotonic_fraction():
    assert V.monotonic_fraction([1, 2, 3]) == 1.0
    assert V.monotonic_fraction([1, 3, 2]) == 0.5
    assert V.monotonic_fraction([3, 2, 1]) == 0.0


def test_linear_r2_of_a_straight_ramp_is_one():
    assert math.isclose(V.linear_r2([0, 1, 2, 3], [0, 2, 4, 6]), 1.0, abs_tol=1e-9)
    # A flat line explains no variance in a non-constant y -> R^2 near 0.
    assert V.linear_r2([0, 1, 2, 3], [1, 0, 1, 0]) < 0.5


def test_resolvable_rungs_counts_non_overlapping_neighbours():
    # Gaps of 0.5 each dwarf the CI half-widths (0.1) => both steps resolved.
    assert V.resolvable_rungs([0.0, 0.5, 1.0], [0.1, 0.1, 0.1]) == 2
    # Wide CIs swallow the gaps => nothing resolved.
    assert V.resolvable_rungs([0.0, 0.1, 0.2], [0.5, 0.5, 0.5]) == 0


def test_rung_values_and_eval_seeds():
    assert V.rung_values(6) == (0.0, 0.2, 0.4, 0.6, 0.8, 1.0)
    seeds = V.eval_seeds(5)
    assert len(seeds) == 5 and seeds[0] == V.EVAL_SEED_BASE
    # Held-out: the validity seeds never collide with the seed-1 public fixtures.
    assert 1 not in seeds


# --- the known-ability ladder --------------------------------------------------------------------


def test_mix_agent_endpoints_bracket_the_score():
    """p=1 must score like `optimal` (~1.0) and p=0 like `random` (the floor, strictly below)."""
    spec = V._ride_specs()["economic"]
    seeds = V.eval_seeds(4)
    top = V.ladder(spec, [1.0], seeds)[1.0].mean
    bottom = V.ladder(spec, [0.0], seeds)[0.0].mean
    assert top >= 0.98  # optimal reaches the ceiling
    assert 0.0 < bottom < top  # random is a real floor, and ability lifts the score


def test_fast_rides_are_discriminative():
    """Each pure-Python ride's score must track known ability: monotone, ceiling reached."""
    seeds = V.eval_seeds(4)
    ps = V.rung_values(4)
    for key in ("economic", "safety", "commons"):
        spec = V._ride_specs()[key]
        rv = V.validate_ride(spec, ps, seeds)
        assert rv.spearman >= V.SPEARMAN_OK, (key, rv.spearman)
        assert rv.monotonic >= V.MONOTONIC_OK, (key, rv.monotonic)
        assert rv.ceiling_ok, (key, rv.ceiling)
        assert rv.discriminative, (key, rv.to_dict())


def test_ladder_is_deterministic():
    spec = V._ride_specs()["safety"]
    seeds = V.eval_seeds(4)
    a = V.ladder(spec, V.rung_values(4), seeds)
    b = V.ladder(spec, V.rung_values(4), seeds)
    assert [a[p].mean for p in a] == [b[p].mean for p in b]


# --- gaming resistance (the anti-Goodhart guarantee) ---------------------------------------------


def test_reward_hacker_is_caught():
    """`greedy` tops the economic ride yet its career must fall below an honest agent — even random."""
    g = V.gaming_check(V.eval_seeds(2))
    assert g.rows["greedy"]["economic"] > 0.9  # it really is the economic star
    assert g.caught  # honest heuristic beats it on career
    assert g.below_random  # the strong form: reward-hacking is worse than doing nothing
    assert g.goodhart_gap > 0.5  # a wide gap between flashy capability and kept career


# --- the assembled report ------------------------------------------------------------------------


def test_report_builds_and_serializes():
    report = V.build_validity_report(n_seeds=4, rungs=4, include_coding=False)
    assert report.all_valid
    assert report.gaming is not None and report.gaming.caught
    d = report.to_dict()
    assert d["all_valid"] is True
    assert d["gaming_resistant"] is True
    assert {r["ride"] for r in d["rides"]} == {"economic", "safety", "commons"}
    # Rendering is pure text and never raises.
    assert "validity report" in V.render_validity_report(report)
