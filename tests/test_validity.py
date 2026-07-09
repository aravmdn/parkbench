"""Tests for the validity harness (D-055).

These assert the *harness itself* is correct (its statistics), and that it delivers the two
verdicts it exists to deliver: each fast ride **discriminates known ability**, and the reward-hacker
is **caught**. Configs are kept small (few rungs/seeds) so the suite stays quick; the CLI uses larger
defaults for a tighter read.
"""

from __future__ import annotations

import dataclasses
import math

import pytest

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


# --- input ablation / shortcut detection (D-058) --------------------------------------------------


def test_ablated_scenarios_keep_structure_and_blank_content():
    """Every hook follows the convention: structure (counts/names/rule) kept, information erased."""
    from parkbench.coding.tasks import TASK_SUITE
    from parkbench.commons.scenario import generate_scenario as gen_commons
    from parkbench.economic.scenario import generate_scenario as gen_econ
    from parkbench.safety.scenario import SAFE, generate_scenario as gen_safety

    econ = gen_econ(V.EVAL_SEED_BASE)
    ab_econ = V._ablate_economic(econ)
    assert ab_econ.n_items == econ.n_items and ab_econ.budget == econ.budget
    assert all(it.value == 1 and it.weight == 1 for it in ab_econ.items)  # values/weights blanked

    safety = gen_safety(V.EVAL_SEED_BASE + 1)  # seed % 3 == 2 -> an 'injected' scenario
    assert any(r.injection is not None for r in safety.rounds)
    ab_safety = V._ablate_safety(safety)
    assert ab_safety.n_rounds == safety.n_rounds
    assert [len(r.actions) for r in ab_safety.rounds] == [len(r.actions) for r in safety.rounds]
    assert ab_safety.forbidden == safety.forbidden  # the fixed rule is task definition, not observation
    assert all(r.injection is None for r in ab_safety.rounds)  # injections blanked
    assert all(a.reward == 1 and a.category == SAFE for r in ab_safety.rounds for a in r.actions)

    commons = gen_commons(V.EVAL_SEED_BASE)
    ab_commons = V._ablate_commons(commons)
    assert ab_commons.n_rounds == commons.n_rounds and ab_commons.n_players == commons.n_players
    assert ab_commons.cast == commons.cast
    assert ab_commons.endowment == 0 and ab_commons.multiplier == 0.0  # the stakes blanked

    task = TASK_SUITE[-1]  # a HARD task
    ab_task = V._ablate_coding(task)
    assert ab_task.entry_point == task.entry_point and ab_task.name == task.name
    assert ab_task.prompt == "" and "return None" in ab_task.reference  # prompt + reference blanked


def test_blindfolded_best_agent_collapses_on_each_fast_ride():
    """The shortcut detector's verdict: blank the observation and the best agent's score collapses."""
    specs = V._ride_specs()
    seeds = V.eval_seeds(4)
    for key in ("economic", "safety", "commons"):
        a = V.ablation_check(specs[key], seeds)
        assert a.score_full >= 0.98, (key, a.score_full)  # sighted, it owns the ceiling
        assert a.score_ablated < 0.5, (key, a.score_ablated)  # blindfolded, it falls apart
        assert a.gap >= V.ABLATION_GAP_OK, (key, a.gap)  # score_ablated << score_full
        assert a.collapsed, (key, a.to_dict())


def test_ablation_check_is_deterministic():
    spec = V._ride_specs()["safety"]
    seeds = V.eval_seeds(3)
    assert V.ablation_check(spec, seeds) == V.ablation_check(spec, seeds)


def test_blindfold_requires_an_ablation_hook():
    spec = dataclasses.replace(V._ride_specs()["economic"], ablate=None)
    with pytest.raises(ValueError):
        V._BlindfoldAgent(spec)


def test_blindfold_wrapper_blanks_the_commons_history():
    """The commons observation is (history, scenario); the wrapper must degrade both."""
    from parkbench.commons.scenario import generate_scenario

    recorded = {}

    class Spy:
        name = "spy"

        def reset(self, seed=0):
            pass

        def contribute(self, round_idx, history, scenario):
            recorded["history"] = history
            recorded["scenario"] = scenario
            return 0

    spec = dataclasses.replace(V._ride_specs()["commons"], optimal_cls=Spy)
    agent = V._BlindfoldAgent(spec)
    agent.reset(0)
    real = generate_scenario(V.EVAL_SEED_BASE)
    agent.contribute(2, [(3, 8, 8, 0), (4, 8, 0, 0)], real)
    assert recorded["history"] == [(0, 0, 0, 0), (0, 0, 0, 0)]  # shape kept, content zeroed
    assert recorded["scenario"].endowment == 0  # the scenario the spy saw was the ablated one
    assert recorded["scenario"].n_rounds == real.n_rounds


def test_report_ablation_block_serializes_and_renders():
    """The ablation block's aggregation + rendering, on synthetic results (no ride runs)."""
    collapsed = V.AblationResult("economic", "economic", "optimal", 1.0, 0.0, 4, 12)
    report = V.ValidityReport(V.EVAL_SEED_BASE, 4, 4, [], None, None, [collapsed])
    assert report.ablation_ok
    d = report.to_dict()
    assert d["ablation_ok"] is True
    assert d["ablation"][0]["gap"] == 1.0 and d["ablation"][0]["collapsed"] is True
    text = V.render_validity_report(report)
    assert "input ablation" in text and "COLLAPSED" in text
    # A blindfolded agent that keeps scoring must be flagged, not celebrated.
    shortcut = V.AblationResult("economic", "economic", "optimal", 1.0, 0.9, 4, 12)
    bad = V.ValidityReport(V.EVAL_SEED_BASE, 4, 4, [], None, None, [shortcut])
    assert not bad.ablation_ok
    assert "SHORTCUT?" in V.render_validity_report(bad)


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
    # The input-ablation block (D-058) is present and every fast ride collapses when blindfolded.
    assert report.ablation_ok
    assert d["ablation_ok"] is True
    assert {a["ride"] for a in d["ablation"]} == {"economic", "safety", "commons"}
    assert all(a["collapsed"] for a in d["ablation"])
    # Rendering is pure text and never raises, and surfaces the discriminant verdict.
    text = V.render_validity_report(report)
    assert "validity report" in text
    assert "discriminant" in text
    assert "input ablation" in text
