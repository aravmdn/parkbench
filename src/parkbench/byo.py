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


@dataclass(frozen=True)
class ByoRun:
    """A completed live BYO run: the wire's own result, shaped for the spectator surfaces.

    ``profile`` is a real :class:`~parkbench.radar.RadarProfile` — built from the single ride the
    wire could score — so ``axes`` / ``missing_axes`` / ``skipped_rides`` are computed by the same
    roll-up code a baseline goes through, not re-derived here.
    """

    identity: AgentIdentity
    profile: RadarProfile
    n_scenarios: int
    round_cap: int
    #: Structural wire provenance (deterministic — no clock, no port). See the module docstring.
    wire: dict = field(default_factory=dict)

    @property
    def agent(self) -> str:
        return self.profile.agent

    @property
    def seed(self) -> int:
        return self.profile.seed

    @property
    def score(self) -> float:
        """The negotiation efficiency this run earned (the only score the wire can produce)."""
        return self.profile.results[0].score if self.profile.results else 0.0

    def to_dict(self) -> dict:
        """The radar-shaped JSON the ``web/`` world consumes for its BYO trainer.

        Identical in shape to ``parkbench radar --json`` (so the front-end needs no second reader),
        plus the three BYO markers the spectator surfaces key off: ``byo``, ``identity`` (D-038) and
        ``live`` — with ``source`` recording *how* it was obtained.
        """
        radar = self.profile.to_dict()
        return {
            "agent": radar["agent"],
            "byo": True,
            "live": True,
            "identity": self.identity.to_dict(),
            "seed": radar["seed"],
            "axes": radar["axes"],
            "missing_axes": radar["missing_axes"],
            "rides": radar["rides"],
            "skipped_rides": radar["skipped_rides"],
            "source": dict(self.wire),
        }


def _other_ride_names() -> list[str]:
    """Every registered ride the BYO wire cannot score, in registry order.

    Imported lazily (as :mod:`parkbench.radar` does) so importing this module never forces the whole
    ride graph to load — and so the list stays correct as rides are added.
    """
    from .rides import RIDE_REGISTRY

    return [name for name in RIDE_REGISTRY if name != WIRE_RIDE]


def run_byo_negotiation(
    agent: Agent,
    *,
    seed: int = 1,
    n_scenarios: int = 12,
    round_cap: int = 8,
    byo_name: str = DEFAULT_BYO_NAME,
    byo_version: Optional[str] = None,
    host: str = "127.0.0.1",
    write_log: bool = False,
    timeout: float = RUN_TIMEOUT_S,
) -> ByoRun:
    """Drive ``agent`` through the negotiation ride **over the wire** and capture its profile.

    Binds a real :class:`~parkbench.server.ParkServer` on an ephemeral loopback port, drives it with
    the reference client, waits for the run to finish and rolls the result up into a
    :class:`ByoRun`. Every observation and action crosses the socket, so this exercises the published
    protocol end-to-end rather than approximating it.

    ``agent`` is whatever plays the BYO side. Over the wire the park cannot tell a genuine third
    party from a built-in stand-in — that indistinguishability *is* the protocol's guarantee (D-015),
    and it is what lets this ship as an offline-verifiable test: point it at a built-in agent here,
    at someone else's HTTP client in the wild.

    ``byo_name`` / ``byo_version`` label the run for attribution (D-038). The ``config_hash`` is the
    driven agent's real one, so two differently-configured BYO agents stay distinguishable.

    Raises ``RuntimeError`` if the park side fails or does not finish inside ``timeout``.
    """
    # Imported lazily: the connector is an optional slice, and the core CLI should not pay for HTTP.
    from .client import drive_agent
    from .rides import NegotiationRide
    from .server import ParkServer
    from .suite import Suite

    counter = _WireCounter(agent)
    suite = Suite(seed=seed, n_scenarios=n_scenarios, round_cap=round_cap)
    server = ParkServer(
        suite, host=host, port=0, agent_name=byo_name, write_log=write_log
    ).start()
    try:
        drive_agent(server.base_url, counter)
        try:
            profile, records = server.wait(timeout=timeout)
        except AssertionError:
            # ParkServer.wait asserts on a profile that never arrived (i.e. we hit `timeout`).
            # A hung wire is an operational failure, not a broken invariant — say so plainly.
            raise RuntimeError(f"BYO run did not finish within {timeout}s") from None
    finally:
        server.stop()

    # Shape the negotiation leg exactly as `NegotiationRide.evaluate` does, so a wired leg and an
    # in-process leg are indistinguishable downstream (asserted in tests/test_byo.py).
    result = RideResult(
        ride=NegotiationRide.name,
        axis=NegotiationRide.axis,
        agent=byo_name,
        score=profile.efficiency.mean,
        detail={
            "efficiency": profile.efficiency.mean,
            "own_value": profile.own_value.mean,
            "deal_rate": profile.deal_rate,
            # Same neutral integrity the in-process ride declares: walking away is legitimate.
            "integrity": 1.0,
        },
    )
    # Build the roll-up through the real RadarProfile so the covered/missing axis split and the
    # skipped-ride list are the radar's own logic, not a second opinion.
    radar_profile = RadarProfile(
        agent=byo_name,
        seed=seed,
        axis_scores={WIRE_AXIS: result.score},
        results=[result],
        skipped=_other_ride_names(),
    )
    inner_identity = counter.identity()
    identity = AgentIdentity(
        name=byo_name,
        version=byo_version or inner_identity.version,
        config_hash=inner_identity.config_hash,
    )
    return ByoRun(
        identity=identity,
        profile=radar_profile,
        n_scenarios=n_scenarios,
        round_cap=round_cap,
        wire={
            "mode": "live",
            "protocol": "http/json",
            "spec": "docs/09-byo-protocol.md",
            "ride": WIRE_RIDE,
            "matches": len(records),
            "turns": counter.turns,
            "driver": counter.name,
        },
    )
