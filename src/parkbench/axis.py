"""Skill axes and the cross-ride result type (decision D-035).

The project's headline output is a per-axis diagnostic *radar profile* (D-007), built from the four
skill families (D-005). A `Ride` reports its result as a `RideResult` carrying its axis and a single
**normalized** headline score in `[0, 1]`, so dissimilar rides can be rolled up onto one radar.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

# The four skill families (D-005) — also the axes of the output radar (D-007).
Axis = Literal["social", "economic", "coding", "safety"]
AXES: tuple[Axis, ...] = ("social", "economic", "coding", "safety")


@dataclass(frozen=True)
class RideResult:
    """One ride's outcome for one agent.

    `score` is the ride's headline metric **normalized to `[0, 1]`** (1 = optimal play), which is
    what makes scores comparable across dissimilar rides for the radar roll-up. `detail` carries the
    ride-specific breakdown (e.g. the full negotiation profile) for drill-down.
    """

    ride: str
    axis: Axis
    agent: str
    score: float
    detail: dict = field(default_factory=dict)
