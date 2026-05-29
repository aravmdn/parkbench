"""The turn-based negotiation engine: runs one bilateral match.

The park orchestrates the loop (decision D-015): on each turn it hands the acting agent
an Observation and receives an Action. The match ends when one side ACCEPTs the other's
standing offer, or when the round cap is reached (decision D-017).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from .protocol import ActionType, Observation, Offer
from .scenario import Scenario


@dataclass
class MatchResult:
    agreed: bool
    outcome: Optional[Offer]
    transcript: list[dict]
    turns_used: int
    round_cap: int


def run_match(scenario: Scenario, agent_a, agent_b, round_cap: int = 8) -> MatchResult:
    """Play one negotiation. Agent A is the test side; agent B is the house persona.

    Agents are expected to have had `.reset(seed, total_rounds)` called beforehand.
    """
    agents = {"A": agent_a, "B": agent_b}
    last_offer: dict[str, Optional[Offer]] = {"A": None, "B": None}
    transcript: list[dict] = []
    max_turns = 2 * round_cap

    for turn in range(max_turns):
        party = "A" if turn % 2 == 0 else "B"
        opp = "B" if party == "A" else "A"
        standing = last_offer[opp]
        obs = Observation(
            role=party,
            my_util=scenario.util_table(party),
            standing_offer=standing,
            my_last_offer=last_offer[party],
            rounds_left=round_cap - (turn // 2),
            history=tuple(transcript),
        )
        action = agents[party].act(obs)

        if action.type == ActionType.ACCEPT and standing is not None:
            transcript.append(
                {"party": party, "type": "accept",
                 "offer": standing.to_dict(), "message": action.message}
            )
            return MatchResult(True, standing, transcript, turn + 1, round_cap)

        if action.type == ActionType.OFFER and action.offer is not None:
            last_offer[party] = action.offer
            transcript.append(
                {"party": party, "type": "offer",
                 "offer": action.offer.to_dict(), "message": action.message}
            )
        else:
            # A MESSAGE, or an ACCEPT with nothing on the table — treated as talk.
            transcript.append({"party": party, "type": "message", "message": action.message})

    return MatchResult(False, None, transcript, max_turns, round_cap)
