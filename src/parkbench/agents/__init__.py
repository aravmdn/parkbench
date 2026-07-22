"""Agent registry and factory."""

from __future__ import annotations

from typing import Callable

from .base import Agent
from .baselines import GreedyAgent, RandomAgent
from .heuristic import HeuristicNegotiator
from .llm import FREE_MODELS, LLMAgent, Provider

# Selector prefix that binds the LLM agent to a specific model: ``llm:<model-id>`` (D-063).
LLM_MODEL_PREFIX = "llm:"


def _llm_factory(model: str) -> Callable[[], Agent]:
    """A zero-arg factory that builds an :class:`LLMAgent` pinned to ``model``.

    Keyless-safe: with no ``OPENROUTER_API_KEY`` the built agent degrades to the deterministic
    heuristic exactly like the bare ``llm`` agent (it never calls the network at construction time).
    """
    return lambda: LLMAgent(model=model)


# Registry values are **zero-arg factories** (an ``Agent`` subclass is itself a zero-arg callable,
# so the baselines register as-is). Curated free-model LLM variants register as factories below.
AGENT_REGISTRY: dict[str, Callable[[], Agent]] = {
    "random": RandomAgent,
    "greedy": GreedyAgent,
    "heuristic": HeuristicNegotiator,
    "llm": LLMAgent,
}

# Expose each curated free model as a selectable ``llm:<model-id>`` agent variant (D-063). All are
# reachable through the SAME single OpenRouter API key — one key unlocks every model, including every
# ":free" one, so this needs no extra keys/accounts. With no key each variant degrades to the
# deterministic heuristic just like the bare ``llm`` agent, so they are always runnable offline.
for _model in FREE_MODELS:
    AGENT_REGISTRY[f"{LLM_MODEL_PREFIX}{_model}"] = _llm_factory(_model)


def make_agent(name: str) -> Agent:
    factory = AGENT_REGISTRY.get(name)
    if factory is not None:
        return factory()
    # Any free model is reachable through the one key, so also honour an *un-curated*
    # ``llm:<model-id>`` selector — ``llm:<any-free-model>`` works without editing the registry.
    if name.startswith(LLM_MODEL_PREFIX) and len(name) > len(LLM_MODEL_PREFIX):
        return LLMAgent(model=name[len(LLM_MODEL_PREFIX):])
    raise ValueError(
        f"Unknown agent '{name}'. Choices: {', '.join(sorted(AGENT_REGISTRY))} "
        f"(or 'llm:<model-id>' for any free OpenRouter model)."
    )


__all__ = [
    "Agent",
    "RandomAgent",
    "GreedyAgent",
    "HeuristicNegotiator",
    "LLMAgent",
    "Provider",
    "FREE_MODELS",
    "LLM_MODEL_PREFIX",
    "AGENT_REGISTRY",
    "make_agent",
]
