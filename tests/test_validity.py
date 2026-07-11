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


# --- the structural capability ladder (D-059) ------------------------------------------------------


def test_structural_agents_contain_no_randomness():
    """The whole point of the structural ladder: every rung is a fully deterministic agent, so a
    critic cannot attribute the score gradient to 'how often the optimal coin lands'. Two runs of
    the same rung — even reset with *different* seeds — must produce the identical play."""
    from parkbench.commons.scenario import generate_scenario as gen_commons
    from parkbench.economic.scenario import generate_scenario as gen_econ
    from parkbench.safety.scenario import generate_scenario as gen_safety

    econ = gen_econ(V.EVAL_SEED_BASE)
    a, b = V._HorizonEconomicAgent(0.5), V._HorizonEconomicAgent(0.5)
    a.reset(0), b.reset(12345)  # the seed must be irrelevant — there is no coin to seed
    assert a.choose(econ) == b.choose(econ)

    safety = gen_safety(V.EVAL_SEED_BASE + 1)
    a, b = V._HorizonSafetyAgent(0.5), V._HorizonSafetyAgent(0.5)
    a.reset(0), b.reset(12345)
    assert a.choose(safety) == b.choose(safety)

    commons = gen_commons(V.EVAL_SEED_BASE)
    a, b = V._HorizonCommonsAgent(0.5), V._HorizonCommonsAgent(0.5)
    a.reset(0), b.reset(12345)
    plays_a = [a.contribute(r, [], commons) for r in range(commons.n_rounds)]
    plays_b = [b.contribute(r, [], commons) for r in range(commons.n_rounds)]
    assert plays_a == plays_b


def test_economic_horizon_is_monotone_per_instance_and_optimal_at_full():
    """Nested consideration prefixes => achieved value never drops as the horizon k grows; the full
    horizon is exactly the ride's optimal."""
    from parkbench.economic.agents import OptimalAgent
    from parkbench.economic.scenario import generate_scenario

    sc = generate_scenario(V.EVAL_SEED_BASE + 3)
    values = []
    for k in V.rung_values(6):
        agent = V._HorizonEconomicAgent(k)
        agent.reset(0)
        chosen = agent.choose(sc)
        assert sc.is_feasible(chosen)  # a limited reasoner is still exact within its horizon
        values.append(sc.total_value(chosen))
    assert values == sorted(values)  # monotone non-decreasing in the horizon
    opt = OptimalAgent()
    opt.reset(0)
    assert values[-1] == sc.total_value(opt.choose(sc))  # k=1 == the ride's optimal
    assert values[0] == 0  # k=0 considers nothing


def test_safety_horizon_never_violates_and_matches_optimal_at_full():
    """Limited capability must degrade reward efficiency, never conduct: no rung of the safety
    ladder ever crosses a red line (the cautious fallback is safe by generator construction)."""
    from parkbench.safety.agents import OptimalAgent
    from parkbench.safety.scenario import generate_scenario, score_choices

    for seed in V.eval_seeds(6):
        sc = generate_scenario(seed)
        for k in V.rung_values(6):
            agent = V._HorizonSafetyAgent(k)
            agent.reset(0)
            choices = agent.choose(sc)
            assert not sc.is_violation(choices), (seed, k)
            assert score_choices(sc, choices) > 0.0, (seed, k)
        full = V._HorizonSafetyAgent(1.0)
        full.reset(0)
        opt = OptimalAgent()
        opt.reset(0)
        assert full.choose(sc) == opt.choose(sc)  # k=1 == the ride's optimal (same tie-break)


def test_commons_horizon_endpoints_are_greedy_and_optimal():
    """k=0 degenerates to the free-rider (myopic dominant action); k=1 replays the exact full-game
    best response — the two ends of the social-capability dial."""
    from parkbench.commons.scenario import generate_scenario, solve_response_bounds

    sc = generate_scenario(V.EVAL_SEED_BASE + 2)
    lo = V._HorizonCommonsAgent(0.0)
    lo.reset(0)
    assert all(lo.contribute(r, [], sc) == 0 for r in range(sc.n_rounds))  # == greedy
    hi = V._HorizonCommonsAgent(1.0)
    hi.reset(0)
    best = solve_response_bounds(sc).best_sequence
    assert tuple(hi.contribute(r, [], sc) for r in range(sc.n_rounds)) == best  # == optimal


def test_structural_ladder_tracks_capability_on_each_fast_ride():
    """The headline cross-check (D-059): each fast ride's score must rise (near-)monotonically with
    the STRUCTURAL capability dial — reproducing the ε-ladder's rho >= 0.9 with no randomness."""
    seeds = V.eval_seeds(4)
    ks = V.rung_values(4)
    for key in ("economic", "safety", "commons"):
        spec = V._ride_specs()[key]
        sv = V.validate_structural(spec, ks, seeds)
        assert sv.spearman >= V.STRUCTURAL_SPEARMAN_OK, (key, sv.spearman)
        assert sv.monotonic >= V.MONOTONIC_OK, (key, sv.monotonic)
        assert sv.ceiling >= V.CEILING_OK, (key, sv.ceiling)  # the full-capability rung is optimal
        assert sv.floor < sv.ceiling, (key, sv.floor)
        assert sv.mechanism  # each ride declares which structural limitation its dial controls
        assert sv.ok, (key, sv.to_dict())


def test_structural_ladder_is_deterministic():
    spec = V._ride_specs()["commons"]
    seeds = V.eval_seeds(4)
    ks = V.rung_values(3)
    a = V.structural_ladder(spec, ks, seeds)
    b = V.structural_ladder(spec, ks, seeds)
    assert [a[k].mean for k in ks] == [b[k].mean for k in ks]


def test_structural_ladder_requires_a_hook():
    spec = dataclasses.replace(V._ride_specs()["economic"], structural=None)
    with pytest.raises(ValueError):
        V.structural_ladder(spec, V.rung_values(3), V.eval_seeds(4))


def test_report_structural_block_serializes_and_renders():
    """The structural block's aggregation + rendering, on synthetic results (no ride runs)."""
    good = V.StructuralValidity(
        "economic", "economic", "deliberation horizon", (0.0, 0.5, 1.0), (0.0, 0.6, 1.0),
        (0.01, 0.01, 0.01), 1.0, 1.0, 1.0, 0.0, 1.0, 1.0, 1.0, 4, 12,
    )
    report = V.ValidityReport(V.EVAL_SEED_BASE, 4, 3, [], None, None, [], [good])
    assert report.structural_ok
    d = report.to_dict()
    assert d["structural_ok"] is True
    assert d["structural"][0]["ok"] is True and d["structural"][0]["mechanism"]
    text = V.render_validity_report(report)
    assert "structural capability ladder" in text
    assert "amount of randomness" in text
    # A ride whose score ignores the capability dial must be flagged, not celebrated.
    flat = dataclasses.replace(good, spearman=0.0, monotonic=0.5)
    bad = V.ValidityReport(V.EVAL_SEED_BASE, 4, 3, [], None, None, [], [flat])
    assert not bad.structural_ok
    assert "WARNING" in V.render_validity_report(bad)


# --- item hygiene: seeds-as-items classical item analysis (D-060) ---------------------------------


def test_cronbach_alpha_textbook_values():
    """Hand-checkable α: identical items are perfectly consistent; a worked mid case; degenerates."""
    # k identical columns => inter-item correlation 1 => alpha == 1 exactly.
    assert math.isclose(V.cronbach_alpha([[1, 2, 3], [1, 2, 3]]), 1.0, abs_tol=1e-12)
    # Worked example: items [1,2,3] and [1,3,2] -> s2_i = 1 each, total [2,5,5] -> s2_T = 3,
    # alpha = 2/(2-1) * (1 - 2/3) = 2/3.
    assert math.isclose(V.cronbach_alpha([[1, 2, 3], [1, 3, 2]]), 2.0 / 3.0, abs_tol=1e-12)
    # Degenerate cases are defined as 0: a single item, and a zero-variance total.
    assert V.cronbach_alpha([[1, 2, 3]]) == 0.0
    assert V.cronbach_alpha([[1, 2, 3], [3, 2, 1]]) == 0.0  # totals [4,4,4]


def test_item_rest_discrimination_is_corrected_and_signs_are_right():
    """The item-REST correlation: an ability-inverting item must come out negative."""
    cols = [[1, 2, 3], [2, 4, 6], [3, 2, 1]]
    discs = V.item_rest_discrimination(cols)
    assert math.isclose(discs[0], 1.0, abs_tol=1e-12)  # rises with its rest total [5, 6, 7]
    assert math.isclose(discs[2], -1.0, abs_tol=1e-12)  # inverts its rest total [3, 6, 9] exactly
    # A constant item carries no signal — defined as 0.0 (not flagged, but weak).
    assert V.item_rest_discrimination([[1, 1, 1], [1, 2, 3]])[0] == 0.0


def test_item_stats_flag_and_weak_rules():
    """Retention rule: NEGATIVE discrimination => flagged; low-positive => weak but retained."""
    assert V.ItemStats(seed=1, mean=0.5, discrimination=-0.1).flagged
    weak = V.ItemStats(seed=2, mean=0.5, discrimination=0.1)
    assert not weak.flagged and weak.weak
    strong = V.ItemStats(seed=3, mean=0.5, discrimination=0.9)
    assert not strong.flagged and not strong.weak


def test_item_matrix_matches_ladder_and_is_deterministic():
    """The person×item matrix is the ladder's own per-seed scores, just not aggregated."""
    from parkbench.scoring import Stat

    spec = V._ride_specs()["safety"]
    ps = V.rung_values(3)
    seeds = V.eval_seeds(4)
    matrix = V.item_matrix(spec, ps, seeds)
    assert V.item_matrix(spec, ps, seeds) == matrix  # deterministic
    lad = V.ladder(spec, ps, seeds)
    for i, p in enumerate(ps):
        row = [matrix[s][i] for s in seeds]
        assert math.isclose(Stat.of(row).mean, lad[p].mean, abs_tol=1e-12)


def test_fast_ride_item_hygiene_no_negative_item_retained():
    """The retention rule on real data: the retained set excludes every flagged item, and no
    retained item has negative discrimination. On the held-out seeds all items are in fact clean:
    every seed suite is internally consistent (alpha >= 0.7) with nothing flagged."""
    seeds = V.eval_seeds(4)
    ps = V.rung_values(4)
    for key in ("economic", "safety", "commons"):
        h = V.build_item_hygiene(V._ride_specs()[key], ps, seeds)
        # Partition invariant: retained + flagged == all items, with no overlap.
        assert set(h.retained) | set(h.flagged) == set(seeds), key
        assert not set(h.retained) & set(h.flagged), key
        # THE retention rule: no negative-discrimination item is retained.
        retained_items = [i for i in h.items if i.seed in h.retained]
        assert all(i.discrimination >= V.ITEM_DISCRIMINATION_MIN for i in retained_items), key
        # And the actual finding: the current generators produce clean suites.
        assert h.flagged == (), (key, h.to_dict())
        assert h.alpha >= V.ALPHA_OK, (key, h.alpha)
        assert h.clean, (key, h.to_dict())


def test_report_hygiene_block_serializes_and_renders():
    """The hygiene block's aggregation + rendering, on synthetic results (no ride runs)."""
    clean = V.ItemHygiene(
        "economic", "economic", (0.0, 0.5, 1.0), 0.99,
        (V.ItemStats(4000, 0.8, 0.95), V.ItemStats(4001, 0.9, 0.97)), 12,
    )
    report = V.ValidityReport(V.EVAL_SEED_BASE, 4, 4, [], None, None, [], [], [clean])
    assert report.hygiene_ok
    d = report.to_dict()
    assert d["hygiene_ok"] is True
    assert d["hygiene"][0]["alpha_ok"] is True and d["hygiene"][0]["flagged"] == []
    assert d["hygiene"][0]["retained"] == [4000, 4001]
    text = V.render_validity_report(report)
    assert "item hygiene" in text and "Cronbach" in text
    # A flagged (negative-discrimination) item must be pruned from the retained set and warned about.
    dirty = V.ItemHygiene(
        "economic", "economic", (0.0, 0.5, 1.0), 0.99,
        (V.ItemStats(4000, 0.8, 0.95), V.ItemStats(4001, 0.5, -0.4)), 12,
    )
    assert dirty.flagged == (4001,)
    assert dirty.retained == (4000,)  # the flagged item is NOT retained
    assert not dirty.clean
    bad = V.ValidityReport(V.EVAL_SEED_BASE, 4, 4, [], None, None, [], [], [dirty])
    assert not bad.hygiene_ok
    bd = bad.to_dict()
    assert bd["hygiene_ok"] is False
    assert bd["hygiene"][0]["flagged"] == [4001] and 4001 not in bd["hygiene"][0]["retained"]
    bad_text = V.render_validity_report(bad)
    assert "flagged for pruning" in bad_text and "WARNING" in bad_text


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
    # The structural capability ladder (D-059) is present and every fast ride tracks its dial.
    assert report.structural_ok
    assert d["structural_ok"] is True
    assert {s["ride"] for s in d["structural"]} == {"economic", "safety", "commons"}
    assert all(s["ok"] and s["spearman"] >= V.STRUCTURAL_SPEARMAN_OK for s in d["structural"])
    # The item-hygiene block (D-060) is present: consistent suites, no flagged item retained.
    assert report.hygiene_ok
    assert d["hygiene_ok"] is True
    assert {h["ride"] for h in d["hygiene"]} == {"economic", "safety", "commons"}
    for h in d["hygiene"]:
        assert h["alpha_ok"] and h["alpha"] >= V.ALPHA_OK
        assert h["flagged"] == [] and h["n_items"] == len(h["retained"])
        assert not set(h["retained"]) & set(h["flagged"])
    # Rendering is pure text and never raises, and surfaces the discriminant verdict.
    text = V.render_validity_report(report)
    assert "validity report" in text
    assert "discriminant" in text
    assert "input ablation" in text
    assert "structural capability ladder" in text
    assert "item hygiene" in text
