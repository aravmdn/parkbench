"""The v1 'good' stand-in test agent (no LLM key required).

A reasonable concession + logrolling negotiator. It exists so we can demonstrate score
discrimination — it should clearly beat the random floor — before any real LLM agent is
wired in (decision D-025).
"""

from __future__ import annotations

from .conceder import ConcederStrategy


class HeuristicNegotiator(ConcederStrategy):
    def __init__(self) -> None:
        super().__init__(name="heuristic", start=0.85, end=0.40, noise=0.0)
