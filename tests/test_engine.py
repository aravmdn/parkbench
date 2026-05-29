from parkbench.agents.base import Agent
from parkbench.engine import run_match
from parkbench.protocol import Action, Offer
from parkbench.scenario import generate_scenario


class FixedOffer(Agent):
    name = "fixed_offer"

    def __init__(self, levels):
        self.levels = levels

    def act(self, obs):
        return Action.make_offer(Offer(self.levels), "fixed")


class EagerAccepter(Agent):
    name = "eager"

    def act(self, obs):
        if obs.standing_offer is not None:
            return Action.accept()
        return Action.make_offer(Offer(tuple(0 for _ in range(obs.n_issues))), "open")


def test_accept_terminates_quickly():
    sc = generate_scenario(1)
    a = FixedOffer(tuple(0 for _ in range(sc.n_issues)))
    b = EagerAccepter()
    a.reset(0, 8)
    b.reset(1, 8)
    res = run_match(sc, a, b, round_cap=8)
    assert res.agreed
    assert res.outcome is not None
    assert res.turns_used == 2          # A offers (turn 0), B accepts (turn 1)


def test_round_cap_yields_no_deal():
    sc = generate_scenario(1)
    # Two stubborn agents that never accept -> exhaust the cap.
    a = FixedOffer(tuple(sc.n_levels - 1 for _ in range(sc.n_issues)))
    b = FixedOffer(tuple(0 for _ in range(sc.n_issues)))
    a.reset(0, 4)
    b.reset(1, 4)
    res = run_match(sc, a, b, round_cap=4)
    assert not res.agreed
    assert res.outcome is None
    assert res.turns_used == 8          # 2 * round_cap
