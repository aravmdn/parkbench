"""Tests for the LLM reference agent (decision D-030).

A FakeProvider returns canned strings so there are NO live network calls. We check:
  - prompt construction includes only the agent's OWN information (D-016);
  - valid JSON parses into the right Action, with well-formed offers; and
  - graceful fallback to the heuristic move on malformed output and on provider errors.
"""

import json

from parkbench.agents import AGENT_REGISTRY, make_agent
from parkbench.agents.heuristic import HeuristicNegotiator
from parkbench.agents.llm import (
    DEFAULT_MODEL,
    LLMAgent,
    OpenRouterProvider,
    Provider,
)
from parkbench.protocol import ActionType, Observation, Offer
from parkbench.scenario import generate_scenario


class FakeProvider(Provider):
    """Returns canned replies; records the messages it was called with."""

    def __init__(self, reply="", raises=False):
        self.reply = reply
        self.raises = raises
        self.calls: list[list[dict]] = []

    def complete(self, messages, **opts):
        self.calls.append(messages)
        if self.raises:
            raise RuntimeError("simulated provider failure")
        return self.reply


def _obs_for(seed=1, role="A", standing=None, rounds_left=8, history=()):
    sc = generate_scenario(seed)
    return Observation(
        role=role,
        my_util=sc.util_table(role),
        standing_offer=standing,
        my_last_offer=None,
        rounds_left=rounds_left,
        history=history,
    )


def test_registered_and_constructible():
    assert "llm" in AGENT_REGISTRY
    assert isinstance(make_agent("llm"), LLMAgent)


def test_default_model_is_free():
    assert DEFAULT_MODEL.endswith(":free")


def test_prompt_contains_only_own_side_info():
    sc = generate_scenario(1)
    obs = _obs_for(seed=1, role="A")
    fake = FakeProvider(reply='{"type":"message","message":"hi"}')
    agent = LLMAgent(provider=fake)
    agent.reset(0, 8)
    agent.act(obs)

    assert len(fake.calls) == 1
    blob = json.dumps(fake.calls[0])
    # Own payoff numbers appear; the counterpart's weights/util must NOT leak.
    assert "my_value_per_issue_level" in blob
    b_table = sc.util_table("B")
    for row in b_table:
        for v in row:
            assert str(round(v, 2)) not in blob or _value_also_in_a(sc, round(v, 2))
    assert "weight_b" not in blob
    assert "util_b" not in blob


def _value_also_in_a(sc, v):
    # A rounded B-value could coincidentally equal a rounded A-value; only then is it OK.
    a_table = sc.util_table("A")
    return any(round(x, 2) == v for row in a_table for x in row)


def test_valid_offer_parses():
    obs = _obs_for(seed=2)
    levels = [1, 0, 2, 1][: obs.n_issues]
    reply = json.dumps({"type": "offer", "levels": levels, "message": "proposal"})
    agent = LLMAgent(provider=FakeProvider(reply=reply))
    agent.reset(0, 8)
    act = agent.act(obs)
    assert act.type == ActionType.OFFER
    assert act.offer == Offer(tuple(levels))
    assert act.message == "proposal"


def test_valid_accept_and_message_parse():
    standing = Offer(tuple(0 for _ in range(4)))
    obs = _obs_for(seed=1, standing=standing)
    acc = LLMAgent(provider=FakeProvider(reply='{"type":"accept","message":"deal"}'))
    acc.reset(0, 8)
    assert acc.act(obs).type == ActionType.ACCEPT

    msg = LLMAgent(provider=FakeProvider(reply='{"type":"message","message":"hello"}'))
    msg.reset(0, 8)
    a = msg.act(obs)
    assert a.type == ActionType.MESSAGE
    assert a.message == "hello"


def test_offer_well_formed_in_range_and_count():
    obs = _obs_for(seed=3)
    levels = [0, 1, 2, 0][: obs.n_issues]
    reply = json.dumps({"type": "offer", "levels": levels})
    agent = LLMAgent(provider=FakeProvider(reply=reply))
    agent.reset(0, 8)
    act = agent.act(obs)
    assert act.type == ActionType.OFFER
    assert len(act.offer.levels) == obs.n_issues
    for i, lv in enumerate(act.offer.levels):
        assert 0 <= lv < len(obs.my_util[i])


def test_json_embedded_in_prose_and_fences():
    obs = _obs_for(seed=2)
    levels = [2, 1, 0, 1][: obs.n_issues]
    inner = json.dumps({"type": "offer", "levels": levels})
    reply = f"Sure, here is my move:\n```json\n{inner}\n```\nHope that works!"
    agent = LLMAgent(provider=FakeProvider(reply=reply))
    agent.reset(0, 8)
    act = agent.act(obs)
    assert act.type == ActionType.OFFER
    assert act.offer == Offer(tuple(levels))


def _heuristic_move(obs):
    h = HeuristicNegotiator()
    h.reset(0, 8)
    return h.act(obs)


def test_fallback_on_malformed_json():
    obs = _obs_for(seed=1)
    agent = LLMAgent(provider=FakeProvider(reply="not json at all"))
    agent.reset(0, 8)
    act = agent.act(obs)
    expected = _heuristic_move(obs)
    assert act.type == expected.type
    if act.type == ActionType.OFFER:
        assert act.offer == expected.offer


def test_fallback_on_wrong_level_count():
    obs = _obs_for(seed=1)
    reply = json.dumps({"type": "offer", "levels": [0]})  # too few
    agent = LLMAgent(provider=FakeProvider(reply=reply))
    agent.reset(0, 8)
    assert agent.act(obs).type == _heuristic_move(obs).type


def test_fallback_on_out_of_range_level():
    obs = _obs_for(seed=1)
    bad = [99] + [0] * (obs.n_issues - 1)
    reply = json.dumps({"type": "offer", "levels": bad})
    agent = LLMAgent(provider=FakeProvider(reply=reply))
    agent.reset(0, 8)
    assert agent.act(obs).type == _heuristic_move(obs).type


def test_fallback_on_provider_exception():
    obs = _obs_for(seed=1)
    agent = LLMAgent(provider=FakeProvider(raises=True))
    agent.reset(0, 8)
    act = agent.act(obs)
    expected = _heuristic_move(obs)
    assert act.type == expected.type
    if act.type == ActionType.OFFER:
        assert act.offer == expected.offer


def test_no_api_key_falls_back_without_network(monkeypatch):
    # No provider injected + no key -> OpenRouterProvider.complete raises -> heuristic.
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    obs = _obs_for(seed=1)
    agent = make_agent("llm")
    agent.reset(0, 8)
    act = agent.act(obs)  # must not raise, must not hang
    assert act.type == _heuristic_move(obs).type


def test_openrouter_provider_reads_env(monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    monkeypatch.setenv("OPENROUTER_MODEL", "some/model:free")
    p = OpenRouterProvider()
    assert p.api_key == "test-key"
    assert p.model == "some/model:free"


def test_openrouter_provider_no_key_raises_not_network(monkeypatch):
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    p = OpenRouterProvider(api_key="")
    try:
        p.complete([{"role": "user", "content": "hi"}])
        raised = False
    except Exception:
        raised = True
    assert raised
