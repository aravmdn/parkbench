from parkbench.engine import MatchResult
from parkbench.protocol import Offer
from parkbench.scenario import Scenario, analyze
from parkbench.scoring import build_profile, score_match


def hand():
    sc = Scenario(("i0", "i1"), 2, (80.0, 20.0), (30.0, 70.0), 0)
    return sc, analyze(sc)


def test_optimal_deal_scores():
    sc, an = hand()
    res = MatchResult(True, Offer((1, 0)), [], 2, 8)
    s = score_match(sc, an, res, "fair")
    assert abs(s.efficiency - 1.0) < 1e-9     # on the welfare frontier
    assert abs(s.own_value - 0.8) < 1e-9      # uA = 80, max_a = 100


def test_no_deal_scores_zero():
    sc, an = hand()
    res = MatchResult(False, None, [], 16, 8)
    s = score_match(sc, an, res, "tough")
    assert s.efficiency == 0.0
    assert s.own_value == 0.0
    assert s.agreed is False


def test_profile_aggregation():
    sc, an = hand()
    good = score_match(sc, an, MatchResult(True, Offer((1, 0)), [], 2, 8), "fair")
    bad = score_match(sc, an, MatchResult(False, None, [], 16, 8), "tough")
    prof = build_profile("x", [good, bad])
    assert prof.deal_rate == 0.5
    assert 0.0 < prof.efficiency.mean < 1.0
    assert prof.efficiency.n == 2
    assert set(prof.per_persona) == {"fair", "tough"}
