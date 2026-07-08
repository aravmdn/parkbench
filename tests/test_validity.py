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


# --- convergent / discriminant validity (MTMM/HTMT, D-057) ---------------------------------------


def _synthetic_convergent(corr_overrides=None):
    """A hand-built matrix so the Campbell-Fiske row/column logic can be tested without ride runs."""
    rides = ("negotiation", "commons", "economic", "safety")
    axes = {
        "negotiation": "social",
        "commons": "social",
        "economic": "economic",
        "safety": "safety",
    }
    scores = {r: {"random": 0.1, "greedy": 0.2, "heuristic": 0.9} for r in rides}
    corr = {
        V._pair_key("negotiation", "commons"): 1.0,  # social monotrait (convergent)
        V._pair_key("negotiation", "economic"): 0.5,
        V._pair_key("negotiation", "safety"): 0.5,
        V._pair_key("commons", "economic"): 0.5,
        V._pair_key("commons", "safety"): 0.5,
        V._pair_key("economic", "safety"): 1.0,  # a HIGH heterotrait pair OUTSIDE the social row/col
    }
    if corr_overrides:
        corr.update({V._pair_key(*k): v for k, v in corr_overrides.items()})
    return V.ConvergentValidity(
        agents=("random", "greedy", "heuristic"),
        rides=rides,
        axes=axes,
        scores=scores,
        correlations=corr,
        n_seeds=8,
        seed_base=V.EVAL_SEED_BASE,
    )


def test_pair_key_is_order_independent():
    assert V._pair_key("a", "b") == V._pair_key("b", "a")


def test_discriminant_uses_only_the_social_row_and_column():
    """Campbell-Fiske: a high heterotrait pair *elsewhere* (economic×safety=1.0) must NOT sink the
    social discriminant — only correlations sharing a ride with the social pair count."""
    cv = _synthetic_convergent()
    assert cv.social_convergent == 1.0
    assert cv.monotrait == [("negotiation", "commons", 1.0)]
    assert ("economic", "safety", 1.0) in cv.heterotrait  # present in the full matrix…
    # …but not in the social row/column, so it does not raise the bar the social pair must clear.
    assert cv.max_social_heterotrait == 0.5
    assert cv.discriminant_ok is True


def test_discriminant_fails_when_a_social_cross_axis_pair_ties_the_monotrait():
    """If a social ride correlates with a different-axis ride as strongly as with its own axis,
    the social axis is NOT shown distinct — discriminant must report failure."""
    cv = _synthetic_convergent(corr_overrides={("commons", "safety"): 1.0})
    assert cv.max_social_heterotrait == 1.0
    assert cv.discriminant_ok is False  # 1.0 > 1.0 is false — no strict separation


def test_negotiation_has_no_optimal_so_shared_roster_is_three():
    """The reason N=3: negotiation's roster has no `optimal`, so it is dropped from the shared set —
    while commons (also social) *does* score optimal. Documents the structural limitation."""
    from parkbench.rides import RIDE_REGISTRY

    seeds = V.eval_seeds(2)
    roster = ("random", "greedy", "heuristic", "optimal")
    neg = V._ride_agent_means(RIDE_REGISTRY["negotiation"], roster, seeds)
    com = V._ride_agent_means(RIDE_REGISTRY["commons"], roster, seeds)
    assert "optimal" not in neg  # negotiation cannot score `optimal`
    assert "optimal" in com  # commons can
    assert set(V.CONVERGENT_ROSTER) == {"random", "greedy", "heuristic"}


def test_convergent_and_discriminant_on_held_out_seeds():
    """The real matrix on held-out eval seeds: the two social rides converge, and that convergence
    exceeds every social-vs-other-axis correlation (discriminant). Stable at >= 8 seeds."""
    cv = V.build_convergent_validity(n_seeds=8)
    assert cv.agents == ("random", "greedy", "heuristic")
    assert cv.social_convergent >= 0.9  # negotiation & commons rank the roster near-identically
    # Every heterotrait value in the social row/column is strictly below the social convergent value.
    for a, b, rho in cv.social_heterotrait:
        assert cv.social_convergent > rho, (a, b, rho)
    assert cv.discriminant_ok is True


def test_convergent_is_deterministic():
    a = V.build_convergent_validity(n_seeds=4)
    b = V.build_convergent_validity(n_seeds=4)
    assert a.scores == b.scores
    assert a.correlations == b.correlations


# --- the assembled report ------------------------------------------------------------------------


def test_report_builds_and_serializes():
    report = V.build_validity_report(n_seeds=8, rungs=4, include_coding=False)
    assert report.all_valid
    assert report.gaming is not None and report.gaming.caught
    d = report.to_dict()
    assert d["all_valid"] is True
    assert d["gaming_resistant"] is True
    assert {r["ride"] for r in d["rides"]} == {"economic", "safety", "commons"}
    # The convergent/discriminant block is present and passes on the default (>= 8) seed count.
    assert report.convergent is not None
    assert d["discriminant_ok"] is True
    cd = d["convergent"]
    assert cd["social_convergent"] >= 0.9
    assert cd["discriminant_ok"] is True
    assert {r["ride"] for r in cd["rides"]} == {"negotiation", "commons", "economic", "safety"}
    assert len(cd["matrix"]) == 6  # 4 rides -> C(4,2) = 6 pairs
    # Rendering is pure text and never raises, and surfaces the discriminant verdict.
    text = V.render_validity_report(report)
    assert "validity report" in text
    assert "discriminant" in text
