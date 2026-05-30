import itertools

from parkbench.agents.heuristic import HeuristicNegotiator
from parkbench.engine import run_match
from parkbench.personas import (
    HOUSE_CAST,
    CooperativePersona,
    FairPersona,
    ToughPersona,
)
from parkbench.protocol import ActionType, Observation, Offer
from parkbench.scenario import analyze, generate_scenario
from parkbench.suite import Suite, run_suite


def _offer_worth_to_b(sc, target_frac):
    """Find the agreement whose value to party B is closest to target_frac of B's max."""
    target = target_frac * analyze(sc).max_b
    best, best_diff = None, float("inf")
    for combo in itertools.product(range(sc.n_levels), repeat=sc.n_issues):
        diff = abs(sc.util_b(combo) - target)
        if diff < best_diff:
            best, best_diff = combo, diff
    return Offer(tuple(best))


def _early_decision(persona_cls, b_table, standing):
    p = persona_cls()
    p.reset(0, 8)
    obs = Observation(role="B", my_util=b_table, standing_offer=standing,
                      my_last_offer=None, rounds_left=8, history=())
    return p.act(obs).type


def test_personas_have_distinct_dispositions():
    sc = generate_scenario(3)
    b_table = sc.util_table("B")
    standing = _offer_worth_to_b(sc, 0.70)  # an offer worth ~70% of B's max to B
    # Early in a match, a cooperative persona takes ~70% while a tough one holds out.
    assert _early_decision(CooperativePersona, b_table, standing) == ActionType.ACCEPT
    assert _early_decision(ToughPersona, b_table, standing) != ActionType.ACCEPT


def test_acceptance_floor_separates_personas_on_one_offer():
    """Reservation floors (D-031): at a single mid-value early offer, the three scripted
    personas split exactly along their floors — cooperative grabs it, fair holds out, tough
    holds out — even though the plain ConcederStrategy would make them all accept."""
    sc = generate_scenario(3)
    b_table = sc.util_table("B")
    standing = _offer_worth_to_b(sc, 0.50)  # worth ~50% of B's max
    assert _early_decision(CooperativePersona, b_table, standing) == ActionType.ACCEPT
    assert _early_decision(FairPersona, b_table, standing) != ActionType.ACCEPT
    assert _early_decision(ToughPersona, b_table, standing) != ActionType.ACCEPT


def test_personas_produce_distinguishable_outcomes():
    """D-031/D-032: against the same test agent on the same suite, the personas must yield
    meaningfully different own-value for party A — they must not collapse to one number.

    Expected ordering of A's captured own-value: tough < fair < cooperative (a tougher
    counterpart leaves the test agent less), with clear, non-overlapping gaps."""
    suite = Suite(seed=1, n_scenarios=12)
    profile, _ = run_suite(suite, HeuristicNegotiator())
    own = {p: v["own_value"].mean for p, v in profile.per_persona.items()}
    # The four personas are genuinely distinct, not collapsed.
    assert len({round(v, 3) for v in own.values()}) == 4
    # Disposition ordering holds with a real gap.
    assert own["tough"] < own["fair"] < own["cooperative"]
    assert own["cooperative"] - own["tough"] > 0.25
    # Each scripted (zero-noise) persona's spread is separated by more than its own CI95.
    tough = profile.per_persona["tough"]
    coop = profile.per_persona["cooperative"]
    assert coop["own_value"].mean - coop["own_value"].ci95 > (
        tough["own_value"].mean + tough["own_value"].ci95
    )


def test_personas_are_deterministic():
    sc = generate_scenario(3)

    def play(cls):
        agent = HeuristicNegotiator()
        persona = cls()
        agent.reset(10, 8)
        persona.reset(11, 8)
        res = run_match(sc, agent, persona, 8)
        return res.agreed, (res.outcome.levels if res.outcome else None)

    for cls in HOUSE_CAST:  # includes Slippery, which uses the RNG
        assert play(cls) == play(cls)
