import itertools

from parkbench.agents.heuristic import HeuristicNegotiator
from parkbench.engine import run_match
from parkbench.personas import HOUSE_CAST, CooperativePersona, ToughPersona
from parkbench.protocol import ActionType, Observation, Offer
from parkbench.scenario import analyze, generate_scenario


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
