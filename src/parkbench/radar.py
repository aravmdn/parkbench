"""The radar roll-up — Parkbench's headline output (decisions D-007, D-037).

A `RadarProfile` is an agent's diagnostic skill profile: one normalized score per **skill axis**
(D-005: ``social`` · ``economic`` · ``coding`` · ``safety``), aggregated from the per-ride
`RideResult`s produced by the ride registry (D-035). Where several rides share an axis, their scores
are **averaged**; an axis with no contributing ride is **absent** (rendered as ``n/a``).

`build_radar` iterates the rides and tolerates rides that cannot score a given agent name (a ride
whose roster does not include that agent raises ``KeyError``/``ValueError``); such rides are
**skipped gracefully** and recorded, so the roll-up never crashes on a partially-covered agent.

This module is **read-only** over the rides: it imports the registry but never mutates it, keeping it
independent of which rides exist (the registry is grown by other slices).
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .axis import AXES, Axis, RideResult

# The exact, deterministic error contract a ride raises when it has no roster entry for an agent
# name. Anything in this tuple is treated as "this ride can't score that agent" → skip gracefully.
_UNSCORABLE = (KeyError, ValueError)


@dataclass(frozen=True)
class RadarProfile:
    """An agent's normalized score per skill axis plus the per-ride breakdown (D-007, D-037).

    - ``axis_scores`` maps each **covered** axis to its aggregated score in ``[0, 1]`` (the mean of
      the contributing rides' normalized scores). Axes with no ride are simply absent.
    - ``results`` is every `RideResult` that contributed, in registry order.
    - ``covered_axes`` / ``missing_axes`` partition the four axes (D-005) by whether any ride scored.
    - ``skipped`` names the rides that declined to score this agent (no roster entry) — surfaced so a
      partially-covered profile is transparent rather than silently thin.
    """

    agent: str
    seed: int
    axis_scores: dict[Axis, float]
    results: list[RideResult] = field(default_factory=list)
    skipped: list[str] = field(default_factory=list)

    @property
    def covered_axes(self) -> list[Axis]:
        """The four axes (in canonical order) that at least one ride scored."""
        return [a for a in AXES if a in self.axis_scores]

    @property
    def missing_axes(self) -> list[Axis]:
        """The four axes (in canonical order) that no ride covered for this agent."""
        return [a for a in AXES if a not in self.axis_scores]

    def to_dict(self) -> dict:
        """A JSON-serializable view of the profile (stable key order for reproducible output)."""
        return {
            "agent": self.agent,
            "seed": self.seed,
            "axes": {a: round(self.axis_scores[a], 6) for a in self.covered_axes},
            "missing_axes": list(self.missing_axes),
            "rides": [
                {
                    "ride": r.ride,
                    "axis": r.axis,
                    "score": round(r.score, 6),
                    "detail": r.detail,
                }
                for r in self.results
            ],
            "skipped_rides": list(self.skipped),
        }


def build_radar(agent_name: str, seed: int = 1, rides=None) -> RadarProfile:
    """Roll the ride registry up into a `RadarProfile` for ``agent_name`` (D-037).

    Iterates ``rides`` (a mapping or iterable of `Ride`s; defaults to
    :data:`parkbench.rides.RIDE_REGISTRY`, injectable for testing), calling each ride's
    ``evaluate(agent_name, seed)``. A ride that cannot score this agent — i.e. raises
    ``KeyError``/``ValueError`` because the name is not in its roster — is **skipped** and its name
    recorded; the roll-up never crashes. Scores are aggregated per axis by **mean** (D-037).

    Deterministic: rides are visited in their registry/iteration order, and a given ``seed`` yields
    an identical profile, so the rendered radar and ``to_dict()`` are reproducible.
    """
    rides = _ride_iter(rides)

    results: list[RideResult] = []
    skipped: list[str] = []
    # axis -> list of contributing scores, kept in visitation order for deterministic averaging.
    by_axis: dict[Axis, list[float]] = {}

    for ride in rides:
        try:
            result = ride.evaluate(agent_name, seed)
        except _UNSCORABLE:
            # This ride has no roster entry for the agent (D-035: each ride owns its roster).
            skipped.append(getattr(ride, "name", repr(ride)))
            continue
        results.append(result)
        by_axis.setdefault(result.axis, []).append(result.score)

    axis_scores: dict[Axis, float] = {
        axis: sum(scores) / len(scores) for axis, scores in by_axis.items()
    }
    return RadarProfile(
        agent=agent_name,
        seed=seed,
        axis_scores=axis_scores,
        results=results,
        skipped=skipped,
    )


def _ride_iter(rides):
    """Normalize the ``rides=`` argument into an iterable of `Ride`s.

    Accepts ``None`` (use the default registry), a mapping (iterate its values, preserving insertion
    order), or any iterable of rides — so tests can inject dummy rides as a list or a dict.
    """
    if rides is None:
        # Imported lazily so importing `radar` never forces the whole ride graph to load.
        from .rides import RIDE_REGISTRY

        rides = RIDE_REGISTRY
    if isinstance(rides, dict):
        return list(rides.values())
    return list(rides)


# --------------------------------------------------------------------------------------------------
# Rendering (stdlib only — no plotting dependency, per D-023)
# --------------------------------------------------------------------------------------------------

_BAR_WIDTH = 24  # characters of full-scale bar for score 1.0


def render_radar(profile: RadarProfile, width: int = _BAR_WIDTH) -> str:
    """A compact, dependency-free per-axis bar chart of the radar profile.

    One row per skill axis (always all four, in canonical D-005 order). Covered axes show a filled
    bar proportional to the score; uncovered axes show ``n/a``. A footer lists the contributing
    rides and any rides skipped for this agent. Pure text — safe to print to any terminal or log.
    """
    lines: list[str] = []
    lines.append(f"Radar profile - agent '{profile.agent}'  (seed={profile.seed})")
    lines.append("")

    label_w = max(len(a) for a in AXES)
    for axis in AXES:
        label = axis.ljust(label_w)
        if axis in profile.axis_scores:
            score = profile.axis_scores[axis]
            filled = round(score * width)
            bar = ("#" * filled).ljust(width)
            lines.append(f"  {label} |{bar}| {score:5.3f}")
        else:
            bar = " " * width
            lines.append(f"  {label} |{bar}|   n/a")

    lines.append("")
    if profile.results:
        ride_bits = ", ".join(f"{r.ride}({r.axis})={r.score:.3f}" for r in profile.results)
        lines.append(f"  rides: {ride_bits}")
    else:
        lines.append("  rides: (none scored this agent)")
    if profile.skipped:
        lines.append(f"  skipped (no roster entry): {', '.join(profile.skipped)}")
    return "\n".join(lines)
