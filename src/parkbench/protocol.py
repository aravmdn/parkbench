"""The wire contract between the park and an agent.

These dataclasses are JSON-serializable and define exactly what a future HTTP/BYO
agent will exchange with the engine (decision D-015). For v1 they are passed in-process.
An `Observation` deliberately carries only the acting agent's OWN utilities — the
counterpart's preferences are private (information asymmetry, decision D-016).
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional


@dataclass(frozen=True)
class Offer:
    """A complete proposal: a chosen level index for every issue, in issue order."""

    levels: tuple[int, ...]

    def to_dict(self) -> dict:
        return {"levels": list(self.levels)}

    @classmethod
    def from_dict(cls, d: dict) -> "Offer":
        return cls(levels=tuple(d["levels"]))


class ActionType(str, Enum):
    MESSAGE = "message"
    OFFER = "offer"
    ACCEPT = "accept"


@dataclass(frozen=True)
class Action:
    """An agent's move on its turn."""

    type: ActionType
    offer: Optional[Offer] = None  # required for OFFER
    message: str = ""

    @staticmethod
    def make_offer(offer: Offer, message: str = "") -> "Action":
        return Action(ActionType.OFFER, offer=offer, message=message)

    @staticmethod
    def accept(message: str = "") -> "Action":
        return Action(ActionType.ACCEPT, message=message)

    @staticmethod
    def say(message: str) -> "Action":
        return Action(ActionType.MESSAGE, message=message)

    def to_dict(self) -> dict:
        return {
            "type": self.type.value,
            "offer": self.offer.to_dict() if self.offer else None,
            "message": self.message,
        }


@dataclass(frozen=True)
class Observation:
    """What an agent sees on its turn. Carries only its OWN utilities."""

    role: str  # "A" (test side) or "B" (house side)
    my_util: tuple[tuple[float, ...], ...]  # my_util[issue][level] -> my payoff contribution
    standing_offer: Optional[Offer]  # the opponent's most recent offer (acceptable as-is)
    my_last_offer: Optional[Offer]
    rounds_left: int  # offers this side may still make, including the current turn
    history: tuple[dict, ...]  # public transcript so far

    @property
    def n_issues(self) -> int:
        return len(self.my_util)

    def my_value(self, offer: Offer) -> float:
        """This agent's payoff for a given full agreement."""
        return sum(self.my_util[i][offer.levels[i]] for i in range(self.n_issues))

    @property
    def my_max(self) -> float:
        """The best payoff this agent could get from any single agreement."""
        return sum(max(row) for row in self.my_util)
