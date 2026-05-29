"""Agent registry and factory."""

from __future__ import annotations

from .base import Agent
from .baselines import GreedyAgent, RandomAgent
from .heuristic import HeuristicNegotiator
from .llm import LLMAgent, Provider

AGENT_REGISTRY: dict[str, type[Agent]] = {
    "random": RandomAgent,
    "greedy": GreedyAgent,
    "heuristic": HeuristicNegotiator,
}


def make_agent(name: str) -> Agent:
    try:
        return AGENT_REGISTRY[name]()
    except KeyError:
        raise ValueError(
            f"Unknown agent '{name}'. Choices: {', '.join(sorted(AGENT_REGISTRY))}"
        ) from None


__all__ = [
    "Agent",
    "RandomAgent",
    "GreedyAgent",
    "HeuristicNegotiator",
    "LLMAgent",
    "Provider",
    "AGENT_REGISTRY",
    "make_agent",
]
