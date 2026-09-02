"""The wire contract for the **commons** ride — a turn loop over a fully public game (D-075).

The park has two BYO wires already and neither fits this ride:

- `protocol.py` (the negotiation wire, D-027) is a turn loop, which is the right *rhythm*, but its
  `Observation` is built around **hidden** information — an agent's own private utility table and the
  counterpart's standing offer (D-016's asymmetry is the point of that ride). A commons round is the
  opposite: every player's contribution is public the moment it is made, and the payoff formula is
  printed on the tin. Reusing that message would mean shipping a private-utility field that is not
  private and a standing-offer field that does not exist.
- `solo_protocol.py` (the plan wire, D-074) has the right *publicity* — the agent sees everything —
  but the wrong rhythm: it hands out a whole instance and takes back one plan. The commons ride is
  sequential on purpose. An agent that answers round by round *while watching what the society did*
  is the entire skill being measured; a one-shot plan would turn a reciprocity game into an open-loop
  guess and quietly change what the ride scores.

So this is a third message shape, and the last one the park needs:

    park: "round 2 of 6; here is what everyone contributed so far"  ->  agent: "I contribute 5"

Same pattern as the other two (**the park drives the loop** — D-015; the agent is a pure HTTP
client), which is what a third-party implementer actually has to learn. With this wire the park's
last *scoreable-by-protocol* gap closes on the social axis: a BYO agent reaches both social rides, so
its `social` axis becomes the same mean of two rides a baseline's is.

## What is on the wire, and why all of it

An observation carries the round index, the whole game, and the **full per-round history including
the house's contributions**. That history is not context-for-flavour: the house cast contains a
grim-trigger reciprocator, and noticing it is the social skill the ride scores. Trimming the history
to the agent's own past — or summarising it — would score the ride at the transport layer by making
the reciprocator invisible.

## What is not on the wire

Nothing is hidden, but nothing is *helpful* either. The park does not send the response bracket, the
best-response sequence, the running payoff, or a hint about which cast member reacts. Those are
scoring internals; a baseline playing in-process cannot see them either (the `optimal` baseline
computes its own), and shipping them would hand a BYO agent a shortcut no in-process agent has.

## Shape only, at the boundary

Like the plan wire, this module checks that a posted contribution is an **integer** and nothing more.
Contributing 0 every round is free-riding — a legitimate, badly-rewarded strategy the ride already
prices — and an out-of-range number is *clamped* by ``commons.scenario.simulate``, exactly as it is
for a built-in agent. Rejecting either with a 400 would hide a real result behind an HTTP error and
inflate a BYO score.
"""

from __future__ import annotations

#: The ride this wire carries. One ride, unlike the plan wire's four: the shape is specific to it.
COMMONS_RIDE = "commons"
COMMONS_AXIS = "social"
COMMONS_TASK = "public-goods"


def scenario_to_dict(scenario) -> dict:
    """Serialize a `CommonsScenario` for the wire (the park side).

    Every field of the frozen dataclass, so ``from_dict(to_dict(s)) == s`` is a real equality
    (asserted in ``tests/test_commons_wire.py``). `threshold` and `levels` are *derived* properties
    and deliberately not sent here — they are rebuilt from the endowment on the agent side, so the
    two ends cannot disagree about them.
    """
    return {
        "task": COMMONS_TASK,
        "seed": scenario.seed,
        "n_players": scenario.n_players,
        "n_rounds": scenario.n_rounds,
        "endowment": scenario.endowment,
        "multiplier": scenario.multiplier,
        # The cast *types* are public: the house is scoring infrastructure (D-004), not a secret.
        # Which of them reacts to the agent is not stated — that is the thing to be discovered.
        "cast": list(scenario.cast),
    }


def scenario_from_dict(payload: dict):
    """Rebuild a `CommonsScenario` from its wire form (the agent side; exact inverse of the above)."""
    from .commons.scenario import CommonsScenario

    return CommonsScenario(
        n_players=int(payload["n_players"]),
        n_rounds=int(payload["n_rounds"]),
        endowment=int(payload["endowment"]),
        multiplier=float(payload["multiplier"]),
        cast=tuple(str(c) for c in payload["cast"]),
        seed=None if payload.get("seed") is None else int(payload["seed"]),
    )


def history_to_list(history) -> list[list[int]]:
    """Serialize the per-round contribution history — player 0 is the agent, then the cast in order."""
    return [[int(c) for c in row] for row in history]


def history_from_list(rows) -> list[tuple[int, ...]]:
    """Rebuild the history in the shape a `CommonsAgent.contribute` expects (a list of tuples)."""
    return [tuple(int(c) for c in row) for row in rows]


def answer_spec(scenario) -> dict:
    """The machine-readable description of the answer this round expects back.

    Mirrors the plan wire's ``answer`` block so a third party meets one convention, not two.
    """
    return {
        "kind": "contribution",
        "of": "units from this round's endowment",
        "range": [0, scenario.endowment],
        # The discretized levels the scoring bracket is solved over. A real agent may contribute any
        # integer in range; these are published because the *bracket* is public, not because the
        # agent is restricted to them.
        "levels": list(scenario.levels),
        "note": (
            "one integer per round, clamped to [0, endowment]; contributing nothing is legal "
            "free-riding and is priced by the ride, not rejected here"
        ),
    }


def contribution_from_dict(payload: dict) -> int:
    """Read a posted contribution off the wire.

    Only the *shape* is checked — a single integer — for the reason in the module docstring: the
    ride, not the transport, is what prices a bad answer.
    """
    if "contribution" not in payload:
        raise ValueError("body must be an object with a 'contribution' integer")
    value = payload["contribution"]
    # `bool` is an `int` subclass in Python; a JSON `true` is not a contribution.
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"contribution must be an integer, got {value!r}")
    return value
