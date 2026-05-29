"""The core v1 claim: a given suite seed reproduces an identical profile."""

from parkbench.agents import make_agent
from parkbench.suite import Suite, run_suite


def _signature(profile):
    return (
        round(profile.efficiency.mean, 9),
        round(profile.own_value.mean, 9),
        round(profile.deal_rate, 9),
        tuple(
            sorted(
                (p, round(v["efficiency"].mean, 9), round(v["own_value"].mean, 9))
                for p, v in profile.per_persona.items()
            )
        ),
    )


def test_heuristic_suite_is_reproducible():
    suite = Suite(seed=1, n_scenarios=6)
    p1, _ = run_suite(suite, make_agent("heuristic"))
    p2, _ = run_suite(suite, make_agent("heuristic"))
    assert _signature(p1) == _signature(p2)


def test_random_agent_is_reproducible_under_seed():
    suite = Suite(seed=2, n_scenarios=6)
    p1, _ = run_suite(suite, make_agent("random"))
    p2, _ = run_suite(suite, make_agent("random"))
    assert _signature(p1) == _signature(p2)


def test_heuristic_beats_random_floor():
    """Discrimination: the 'good' agent should out-score the random floor overall."""
    suite = Suite(seed=1, n_scenarios=12)
    good, _ = run_suite(suite, make_agent("heuristic"))
    floor, _ = run_suite(suite, make_agent("random"))
    # Heuristic should capture more joint value and close more deals than random.
    assert good.efficiency.mean > floor.efficiency.mean
    assert good.deal_rate >= floor.deal_rate
