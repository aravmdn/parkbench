"""Provider-agnostic LLM agent seam (decision D-025).

The provider is intentionally left unimplemented for v1 core. To wire a real reference
agent (or to let a bring-your-own agent run), implement `Provider.complete` for your
LLM of choice and finish `LLMAgent.act`'s prompt construction + action parsing. The
open design points are tracked in docs/04-open-questions.md.
"""

from __future__ import annotations

import abc
from typing import Optional

from ..protocol import Action, Observation
from .base import Agent


class Provider(abc.ABC):
    """Adapter to a chat LLM. Implement this to plug in Anthropic / OpenAI / etc."""

    @abc.abstractmethod
    def complete(self, system: str, prompt: str) -> str:
        ...


class LLMAgent(Agent):
    name = "llm"

    def __init__(self, provider: Optional[Provider] = None) -> None:
        self.provider = provider

    def act(self, obs: Observation) -> Action:
        if self.provider is None:
            raise NotImplementedError(
                "LLMAgent has no Provider configured. Wire an LLM provider before "
                "using the 'llm' agent (see docs/04-open-questions.md)."
            )
        raise NotImplementedError(
            "LLM prompt construction and action parsing are deferred past v1 core."
        )
