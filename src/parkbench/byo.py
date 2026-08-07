"""Live BYO connector — drive a third-party agent over the real wire and capture its profile.

The world (``web/``) has rendered a **bring-your-own** trainer since D-063, but its numbers came from
a hand-authored ``radar-byo.json`` stand-in. This module closes that gap: it runs a BYO agent through
the **actual** HTTP/JSON protocol documented in ``docs/09-byo-protocol.md`` — a real
:class:`parkbench.server.ParkServer` bound to an ephemeral loopback port, driven by the reference
client :func:`parkbench.client.drive_agent` — and shapes the completed run into the same
radar-shaped JSON the spectator surfaces already consume. Nothing is simulated: the observations,
actions and the ``done`` payload all cross a socket.

> **Presentation-only in spirit (D-012), reuse-only in fact.** This module computes **no** score. The
> negotiation is played by the existing ``engine``/``suite``, scored by the existing ``scoring``, and
> rolled up by the existing :class:`parkbench.radar.RadarProfile`. The connector's whole job is
> *transport + shaping*, which is why a wired run reproduces the in-process
> :class:`parkbench.rides.NegotiationRide` result exactly (pinned in ``tests/test_byo.py``).

## The honest shape of a live BYO profile

A baseline's radar covers all four axes because the engine can run it through all seven rides
in-process. **A BYO agent reached over the wire cannot be**: the v1 protocol carries the
*negotiation* ride only (``docs/09``, "Scope" — the solo rides are scored from submitted
artifacts/agents in-process, not over this wire). So a live BYO profile honestly covers exactly one
axis:

- ``axes`` — ``{"social": <negotiation efficiency>}`` and nothing else.
- ``missing_axes`` — ``["economic", "coding", "safety"]``.
- ``skipped_rides`` — every other registered ride, because none of them can score this agent.

That is a *narrower* profile than the hand-authored stand-in it replaces, which claimed scores on all
five rides it had no way to earn. Narrow-and-true beats wide-and-invented: the front-end draws the
missing axes as ``n/a`` rather than zero, so a spectator can see what was actually measured.

## Determinism

The payload carries **no timestamp and no port** — two runs of the same agent at the same seed
produce byte-identical JSON, exactly like every other Parkbench result. Provenance is recorded
structurally instead (protocol, ride, match/turn counts), so a captured profile stays comparable and
diffable. The ephemeral port and the wall-clock are run *mechanics*, not run *results*.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from .agents.base import Agent, AgentIdentity
from .axis import RideResult
from .protocol import Action, Observation
from .radar import RadarProfile

#: The BYO trainer the visual world already renders (D-063) — the default label for a captured run.
DEFAULT_BYO_NAME = "acme-bot"

#: Ceiling on how long the park side may take to finish a run before we call it a failure. Generous:
#: a 12-scenario suite over loopback takes ~1 s, so this only ever fires on a genuine hang.
RUN_TIMEOUT_S = 120.0

#: The one ride the v1 BYO wire can score (``docs/09-byo-protocol.md`` "Scope").
WIRE_RIDE = "negotiation"
WIRE_AXIS = "social"


class _WireCounter(Agent):
    """Transparent proxy that counts the turns the BYO client answered over the wire.

    Wraps the agent being driven so the captured run can report *how much protocol traffic actually
    happened* — the one honest signal that a profile came from the wire rather than from a fixture.
    It delegates everything and decides nothing, so the wrapped agent's behaviour (and therefore the
    score) is untouched.
    """

    def __init__(self, inner: Agent) -> None:
        self.inner = inner
        self.name = inner.name
        self.version = getattr(inner, "version", None) or "0"
        self.turns = 0
        self.matches = 0

    def reset(self, seed: int = 0, total_rounds: int = 8) -> None:
        self.matches += 1
        self.inner.reset(seed=seed, total_rounds=total_rounds)

    def act(self, obs: Observation) -> Action:
        self.turns += 1
        return self.inner.act(obs)

    def config(self) -> dict:
        return self.inner.config()

    def identity(self) -> AgentIdentity:
        return self.inner.identity()
