"""Live BYO connectors — drive a third-party agent over the real wires and capture its profile.

The world (``web/``) has rendered a **bring-your-own** trainer since D-063, but its numbers came from
a hand-authored ``radar-byo.json`` stand-in. This module closes that gap: it runs a BYO agent through
the **actual** HTTP/JSON protocols documented in ``docs/09-byo-protocol.md`` — real servers bound to
ephemeral loopback ports, driven by the reference clients — and shapes the completed run into the
same radar-shaped JSON the spectator surfaces already consume. Nothing is simulated: every
observation, scenario, action, plan and ``done`` payload crosses a socket.

Two wires, so three entry points:

- :func:`run_byo_negotiation` — one leg over the negotiation wire (D-027/D-073).
- :func:`run_byo_solo` — one leg over the solo wire (D-074).
- :func:`run_byo_profile` — sweep both, and roll the legs up into one radar.

> **Presentation-only in spirit (D-012), reuse-only in fact.** This module computes **no** score.
> Each ride is played and scored by its own existing code — the negotiation by ``engine``/``suite``
> and ``scoring``, each solo ride by its own ``run_suite`` reached through the ride's own
> ``evaluate(..., agent=...)`` — and rolled up by the existing
> :class:`parkbench.radar.RadarProfile`. The connectors' whole job is *transport + shaping*, which is
> why a wired leg reproduces the in-process ride exactly (pinned in ``tests/test_byo.py`` and
> ``tests/test_solo_wire.py``).

## The honest shape of a live BYO profile

A baseline's radar covers all four axes because the engine can run it through all seven rides
in-process. **A BYO agent reached over the wire covers only the rides a wire exists for**, and there
are two (``docs/09``):

- the **negotiation** wire (`server.py` / `client.py`, D-027) — one ride, the ``social`` axis;
- the **solo** wire (`solo_server.py` / `solo_client.py`, D-074) — the four plan-shaped rides
  ``economic`` · ``exchange`` · ``safety`` · ``containment``, i.e. *both* rides on the ``economic``
  axis and *both* rides on the ``safety`` axis.

So there are two honest live shapes, and the caller picks:

- :func:`run_byo_negotiation` — the D-073 single-leg capture. ``axes`` = ``{"social": ...}``;
  ``missing_axes`` = ``["economic", "coding", "safety"]``.
- :func:`run_byo_profile` — the full wire sweep. ``axes`` = ``social`` · ``economic`` · ``safety``;
  ``missing_axes`` = ``["coding"]``; ``skipped_rides`` = ``["commons", "coding"]``, the two rides no
  wire carries (a sequential multi-agent game and a submit-an-artifact task — see
  :data:`parkbench.solo_protocol.UNREACHABLE_RIDES`).

Either way the profile is a *narrower* one than the hand-authored stand-in D-073 replaced, which
claimed scores on all five rides it had no way to earn. Narrow-and-true beats wide-and-invented: the
front-end draws the missing axes as ``n/a`` rather than zero, so a spectator sees what was actually
measured. What D-074 changes is only *how* narrow: three axes instead of one.

Note what a three-axis profile still is **not**: a career. The career roll-up (D-041) multiplies an
``integrity`` signal from *every* ride, so an agent that cannot be run on ``coding`` and ``commons``
has no such product and stays off the leaderboard — correctly, and by the same rule that applies to
a baseline.

## Determinism

The payload carries **no timestamp and no port** — two runs of the same agent at the same seed
produce byte-identical JSON, exactly like every other Parkbench result. Provenance is recorded
structurally instead (protocol, ride(s), match/turn counts, and for a sweep the per-leg breakdown
plus the named unreachable rides), so a captured profile stays comparable and diffable. The ephemeral
port and the wall-clock are run *mechanics*, not run *results*.
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

#: The one ride the *negotiation* BYO wire can score (``docs/09-byo-protocol.md`` "Scope").
WIRE_RIDE = "negotiation"
WIRE_AXIS = "social"

def _solo_wire_rides() -> tuple[str, ...]:
    """The rides the *solo* BYO wire can score, in registry order (D-074).

    Read from :mod:`parkbench.solo_protocol` rather than restated here, so putting a ride on that
    wire reaches the connector, the CLI and the endpoint without a second edit.
    """
    from .solo_protocol import SOLO_RIDES

    return tuple(SOLO_RIDES)


def _all_wire_rides() -> tuple[str, ...]:
    """Every ride reachable over some BYO wire, in the order a full sweep drives them."""
    return (WIRE_RIDE,) + _solo_wire_rides()


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

    ``profile`` is a real :class:`~parkbench.radar.RadarProfile` — built from whichever rides a wire
    could score — so ``axes`` / ``missing_axes`` / ``skipped_rides`` are computed by the same roll-up
    code a baseline goes through, not re-derived here.
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
        """The **first** leg's score — the negotiation efficiency for a single-leg capture.

        A full sweep (:func:`run_byo_profile`) has one score per ride, so read ``profile.results``
        or ``profile.axis_scores`` for those rather than collapsing them into a headline number the
        radar deliberately does not define.
        """
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


def _other_ride_names(covered=(WIRE_RIDE,)) -> list[str]:
    """Every registered ride not in ``covered``, in registry order.

    Imported lazily (as :mod:`parkbench.radar` does) so importing this module never forces the whole
    ride graph to load — and so the list stays correct as rides are added: a ride added to the
    registry but not to a wire shows up as skipped on the next captured profile, rather than
    silently vanishing from the honesty report.
    """
    from .rides import RIDE_REGISTRY

    covered = set(covered)
    return [name for name in RIDE_REGISTRY if name not in covered]


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


def run_byo_from_name(agent_name: str, **kwargs) -> ByoRun:
    """:func:`run_byo_negotiation` for an agent named in the negotiation registry.

    Convenience for the CLI and the ``/byo`` endpoint — the wire is agent-agnostic, so any built-in
    negotiator can stand in for a third party while the protocol path stays identical.
    """
    from .agents import make_agent

    return run_byo_negotiation(make_agent(agent_name), **kwargs)


def run_byo_solo(
    ride: str,
    agent,
    *,
    seed: int = 1,
    byo_name: str = DEFAULT_BYO_NAME,
    host: str = "127.0.0.1",
    timeout: float = RUN_TIMEOUT_S,
) -> tuple[RideResult, dict]:
    """Drive ``agent`` through one **solo** ride over the wire (D-074); return its result + provenance.

    The solo analogue of :func:`run_byo_negotiation`. Binds a real
    :class:`~parkbench.solo_server.SoloParkServer` on an ephemeral loopback port, drives it with the
    reference client :func:`~parkbench.solo_client.drive_solo_agent`, and returns the
    :class:`~parkbench.axis.RideResult` the **ride itself** produced — the server runs
    ``RIDE_REGISTRY[ride].evaluate(..., agent=<bridge>)``, so nothing about the scoring is
    re-implemented here and a wired leg equals an in-process leg exactly, ``detail`` included.

    ``agent`` is any object with that ride's agent shape (``reset(seed=...)`` + ``choose(scenario)``)
    — over the wire the park cannot tell a genuine third party from a built-in stand-in, which is
    what lets this ship as an offline-verifiable test.

    Raises ``ValueError`` for a ride the solo wire does not carry, and ``RuntimeError`` if the park
    side fails or does not finish inside ``timeout``.
    """
    # Imported lazily: the connector is an optional slice, and the core CLI should not pay for HTTP.
    from .solo_client import drive_solo_agent
    from .solo_protocol import spec_for
    from .solo_server import SoloParkServer

    spec = spec_for(ride)  # fail fast, by name, before binding a socket
    server = SoloParkServer(ride, seed=seed, host=host, agent_name=byo_name).start()
    try:
        drive_solo_agent(server.base_url, agent, timeout=timeout)
        result = server.wait(timeout=timeout)
    finally:
        server.stop()

    return result, {
        "ride": ride,
        "wire": "solo",
        "task": spec.task,
        "steps": server.agent.steps,
    }


def run_byo_profile(
    agent_name: str = "heuristic",
    *,
    seed: int = 1,
    n_scenarios: int = 12,
    round_cap: int = 8,
    byo_name: str = DEFAULT_BYO_NAME,
    byo_version: Optional[str] = None,
    rides: Optional[tuple[str, ...]] = None,
    host: str = "127.0.0.1",
    timeout: float = RUN_TIMEOUT_S,
) -> ByoRun:
    """Sweep a BYO agent across **every wire the park has** and capture the multi-axis profile (D-074).

    Runs the negotiation wire (D-073) and then each solo ride's wire (D-074) in turn, each on its own
    ephemeral loopback port, and rolls the legs up through the real
    :class:`~parkbench.radar.RadarProfile`. With the full default set of rides that is a **three-axis**
    profile — ``social`` (negotiation) · ``economic`` (knapsack + exchange) · ``safety`` (red-line +
    containment) — with ``coding`` honestly missing and ``commons``/``coding`` listed as skipped.

    ``agent_name`` is resolved **per ride from that ride's own roster** (D-035: each ride owns its
    agent interface), exactly as :func:`parkbench.radar.build_radar` does for a baseline. A real third
    party is one HTTP client that answers every wire; a built-in stand-in needs one object per ride,
    and the transport cannot tell the difference.

    Deterministic like every other Parkbench result: no clock, no port, no ordering surprises — the
    same agent at the same seed emits byte-identical JSON.
    """
    ride_names = tuple(rides) if rides is not None else _all_wire_rides()
    # Resolve every driver up front, so a name one ride's roster lacks fails by name before any
    # socket is bound or any suite is run — rather than half-way through a sweep. (`optimal` is the
    # live case: every solo ride has one, the negotiation cast has none.)
    agents = {ride: _agent_for_ride(ride, agent_name) for ride in ride_names}

    results: list[RideResult] = []
    legs: list[dict] = []
    matches = 0
    turns = 0
    driver = agent_name

    for ride in ride_names:
        if ride == WIRE_RIDE:
            neg = run_byo_negotiation(
                agents[ride],
                seed=seed,
                n_scenarios=n_scenarios,
                round_cap=round_cap,
                byo_name=byo_name,
                byo_version=byo_version,
                host=host,
                timeout=timeout,
            )
            results.extend(neg.profile.results)
            legs.append(
                {
                    "ride": WIRE_RIDE,
                    "wire": "negotiation",
                    "task": "bilateral-bargaining",
                    "matches": neg.wire["matches"],
                    "turns": neg.wire["turns"],
                }
            )
            matches += int(neg.wire["matches"])
            turns += int(neg.wire["turns"])
            driver = neg.wire["driver"]
            continue

        result, leg = run_byo_solo(
            ride,
            agents[ride],
            seed=seed,
            byo_name=byo_name,
            host=host,
            timeout=timeout,
        )
        # The ride's own `evaluate` labels the result with the *roster name* it was asked for; the
        # run belongs to the BYO agent, so relabel it (and nothing else) for attribution.
        results.append(
            RideResult(
                ride=result.ride,
                axis=result.axis,
                agent=byo_name,
                score=result.score,
                detail=result.detail,
            )
        )
        legs.append(leg)
        matches += int(leg["steps"])
        turns += int(leg["steps"])

    profile = _radar_from_results(byo_name, seed, results)
    identity = _byo_identity(byo_name, byo_version, agent_name)
    return ByoRun(
        identity=identity,
        profile=profile,
        n_scenarios=n_scenarios,
        round_cap=round_cap,
        wire={
            "mode": "live",
            "protocol": "http/json",
            "spec": "docs/09-byo-protocol.md",
            # A single string for the surfaces that print one (the world's stats screen), and the
            # per-leg breakdown right beside it for anything that wants the detail.
            "ride": "+".join(r.ride for r in results),
            "rides": legs,
            "matches": matches,
            "turns": turns,
            "driver": driver,
            # Named, not silently omitted: the two rides no wire carries, with the reason.
            "unreachable": _unreachable_note(),
        },
    )


def _negotiation_agent(agent_name: str):
    """The negotiation-roster agent for ``agent_name`` (the BYO stand-in on the D-027 wire)."""
    from .agents import make_agent

    return make_agent(agent_name)


def _solo_agent(ride: str, agent_name: str):
    """The ``ride``-roster agent for ``agent_name`` (each ride owns its agent interface, D-035)."""
    from importlib import import_module

    return import_module(f".{ride}", __package__).make_agent(agent_name)


def _agent_for_ride(ride: str, agent_name: str):
    """Resolve ``agent_name`` against ``ride``'s own roster, failing with a message that names both.

    Rosters differ by ride on purpose (D-035) — the negotiation cast has no `optimal`, because
    nothing plays a negotiation perfectly — so "which agent" is only answerable per ride. The raw
    `KeyError` a registry raises says neither the ride nor what it does have.
    """
    try:
        return _negotiation_agent(agent_name) if ride == WIRE_RIDE else _solo_agent(ride, agent_name)
    except (KeyError, ValueError):
        raise ValueError(f"ride {ride!r} has no agent named {agent_name!r} in its roster") from None


def _unreachable_note() -> dict:
    from .solo_protocol import UNREACHABLE_RIDES

    return dict(UNREACHABLE_RIDES)


def _radar_from_results(byo_name: str, seed: int, results: list[RideResult]) -> RadarProfile:
    """Roll captured legs up with the radar's own per-axis mean (D-037) — no second aggregation."""
    by_axis: dict[str, list[float]] = {}
    for r in results:
        by_axis.setdefault(r.axis, []).append(r.score)
    return RadarProfile(
        agent=byo_name,
        seed=seed,
        axis_scores={axis: sum(v) / len(v) for axis, v in by_axis.items()},
        results=results,
        skipped=_other_ride_names(covered=[r.ride for r in results]),
    )


def _byo_identity(byo_name: str, byo_version: Optional[str], agent_name: str) -> AgentIdentity:
    """The D-038 identity for a captured sweep: the BYO label over the driven agent's real hash.

    The negotiation roster is asked first because its agents carry a real ``identity()`` (D-038) and
    hash their own defining config, so two differently-configured drivers stay distinguishable. A
    sweep that drives **only** solo rides can name an agent that roster does not have (`optimal` is
    the live case — it exists on every solo ride and on none of the negotiation cast), and the solo
    agent classes predate D-038 and have no ``identity()``. Rather than crash, fall back to hashing
    the driver name: still deterministic, still distinguishes drivers, just with less to hash.
    """
    from . import __version__ as package_version
    from .agents import AGENT_REGISTRY
    from .agents.base import config_hash

    if agent_name in AGENT_REGISTRY:
        inner = _negotiation_agent(agent_name).identity()
        return AgentIdentity(
            name=byo_name,
            version=byo_version or inner.version,
            config_hash=inner.config_hash,
        )
    return AgentIdentity(
        name=byo_name,
        version=byo_version or package_version or "0",
        config_hash=config_hash({"driver": agent_name}),
    )


def render_byo_run(run: ByoRun) -> str:
    """A compact text summary of a captured live BYO run (the CLI's default output)."""
    ident = run.identity
    lines = [
        f"BYO live run - '{ident.name}'  (seed={run.seed})",
        "",
        f"  identity      : {ident.name} v{ident.version} #{ident.config_hash}  (D-038)",
        f"  wire          : {run.wire.get('protocol')} per {run.wire.get('spec')}"
        f"  ({run.wire.get('matches')} scored units, {run.wire.get('turns')} turns answered)",
        f"  driven by     : {run.wire.get('driver')}",
        "",
    ]
    # One row per leg the wire actually scored. A single-leg (D-073) capture therefore still prints
    # exactly its one negotiation line; a full sweep (D-074) prints all five.
    label_w = max((len(r.ride) for r in run.profile.results), default=11)
    for result in run.profile.results:
        lines.append(f"  {result.ride.ljust(label_w)} : {result.score:.6f}   ({result.axis} axis)")
    if not run.profile.results:
        lines.append("  (no ride scored this agent)")
    lines += [
        "",
        f"  covered axes  : {', '.join(run.profile.covered_axes) or '(none)'}",
        f"  missing axes  : {', '.join(run.profile.missing_axes) or '(none)'}   "
        f"[not reachable over the BYO wires]",
        f"  skipped rides : {', '.join(run.profile.skipped) or '(none)'}",
    ]
    unreachable = run.wire.get("unreachable", {})
    if unreachable:
        # Distinguish "no wire carries this" from "this run simply did not drive that wire" — the
        # skipped list above holds both, and only the former is a limit of the protocol.
        lines.append("    no wire carries:")
        for ride, why in sorted(unreachable.items()):
            lines.append(f"    - {ride}: {why}")
    return "\n".join(lines)
