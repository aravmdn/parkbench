from parkbench.scenario import (
    SCENARIO_SHAPES,
    Scenario,
    analyze,
    generate_scenario,
    shape_for_index,
)
from parkbench.suite import Suite


def hand_scenario() -> Scenario:
    # 2 issues, 2 levels. A weights [80, 20] (prefers high), B weights [30, 70] (prefers low).
    return Scenario(issues=("i0", "i1"), n_levels=2,
                    weight_a=(80.0, 20.0), weight_b=(30.0, 70.0), seed=0)


def test_utilities_hand_values():
    sc = hand_scenario()
    assert sc.util_a((1, 0)) == 80.0          # A takes its high-value issue
    assert sc.util_b((1, 0)) == 70.0          # B takes its high-value issue
    assert sc.util_a((1, 1)) == 100.0         # everything A's way
    assert sc.util_b((0, 0)) == 100.0         # everything B's way


def test_analysis_optimum():
    an = analyze(hand_scenario())
    assert an.max_joint == 150.0              # = max(80,30) + max(20,70)
    assert an.max_a == 100.0
    assert an.max_b == 100.0
    assert an.nash_outcome == (1, 0)          # the logrolling deal


def test_generated_scenario_is_integrative():
    sc = generate_scenario(1, n_issues=4, n_levels=3)
    an = analyze(sc)
    # Jointly achievable value exceeds what either side can get alone -> trades exist.
    assert an.max_joint > an.max_a
    assert an.max_joint > an.max_b
    assert abs(sum(sc.weight_a) - 100.0) < 1e-6
    assert abs(sum(sc.weight_b) - 100.0) < 1e-6


def test_generation_is_deterministic():
    a = generate_scenario(5)
    b = generate_scenario(5)
    assert a == b


def test_weights_are_moderately_dispersed():
    """D-032: weights are ranked (some issues matter more) but no issue dominates — the
    largest weight stays well below the degenerate 'one issue is everything' regime."""
    for seed in range(20):
        sc = generate_scenario(seed, n_issues=5, n_levels=4)
        assert len(set(sc.weight_a)) == sc.n_issues  # genuinely ranked, no ties
        # Moderate dispersion: no single issue is worth more than ~half the total (100).
        assert max(sc.weight_a) < 50.0
        assert max(sc.weight_b) < 50.0
        # Anti-correlation still holds: A's smallest-weight issue is B's largest.
        a_min_issue = min(range(sc.n_issues), key=lambda i: sc.weight_a[i])
        b_max_issue = max(range(sc.n_issues), key=lambda i: sc.weight_b[i])
        assert a_min_issue == b_max_issue


def test_suite_varies_scenario_shapes():
    """D-032: the canonical suite cycles issue/level counts instead of a single fixed shape,
    and every shape stays inside the D-016 envelope (3-5 issues)."""
    suite = Suite(seed=1, n_scenarios=12)  # vary_shapes defaults to True
    shapes = {suite.shape(i) for i in range(suite.n_scenarios)}
    assert len(shapes) >= 4  # more than one shape exercised
    for n_issues, n_levels in shapes:
        assert 3 <= n_issues <= 5
        assert 2 <= n_levels <= 5
    # shape_for_index mirrors the suite and cycles the SCENARIO_SHAPES menu.
    assert suite.shape(0) == shape_for_index(0) == SCENARIO_SHAPES[0]


def test_suite_can_pin_a_fixed_shape():
    """vary_shapes=False falls back to the explicit n_issues/n_levels (for reproducible
    single-shape experiments)."""
    suite = Suite(seed=1, n_scenarios=3, n_issues=4, n_levels=3, vary_shapes=False)
    assert {suite.shape(i) for i in range(3)} == {(4, 3)}
