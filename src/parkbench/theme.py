"""The park skin - a pure presentation layer over the rides (decision D-046).

D-012 deferred the creative theme until the mechanics were right ("mechanics first, theme later").
With five scored rides, the four-axis radar, and the career all in place, this module applies the
**theme-park skin** - and *only* the skin. It maps each scored ride (`parkbench.rides.RIDE_REGISTRY`)
to a themed **attraction** and each skill axis (D-005) to a themed **land**, then renders an ASCII
**park map**. It is deliberately presentation-only: it never imports scoring/engine code and never
changes a number - so the skin can never affect a result (the whole point of D-012).

The one real invariant it enforces is *coverage*: every registered ride must have an attraction (see
`attraction_for` and the theme tests), so a new ride can't ship un-themed.
"""

from __future__ import annotations

from dataclasses import dataclass

from .axis import AXES, Axis


@dataclass(frozen=True)
class Land:
    """A themed district of the park - one per skill axis (D-005)."""

    axis: Axis
    name: str
    blurb: str


@dataclass(frozen=True)
class Attraction:
    """A themed face for one scored ride. ``ride`` is the registry key (the link back to mechanics)."""

    ride: str
    marquee: str
    tagline: str
    icon: str


# The four skill axes (D-005), skinned as the park's four lands.
LANDS: dict[Axis, Land] = {
    "social": Land("social", "Society Square", "Where agents deal, cooperate, and connive."),
    "economic": Land("economic", "Market Midway", "Scarcity, budgets, and the hunt for value."),
    "coding": Land("coding", "Maker's Workshop", "Build it, ship it, survive the tests."),
    "safety": Land("safety", "Safety Gauntlet", "Hold the line when the rewards pull you across it."),
}

# One attraction per scored ride. Keyed by the ride's registry name so the skin tracks the mechanics.
ATTRACTIONS: dict[str, Attraction] = {
    "negotiation": Attraction(
        "negotiation",
        "The Bargaining Bazaar",
        "Strike multi-issue deals with the house cast - find the trades, hold your share.",
        "[$]",
    ),
    "commons": Attraction(
        "commons",
        "The Commons Carousel",
        "Cooperate or free-ride in a public-goods showdown - the crowd remembers.",
        "(O)",
    ),
    "economic": Attraction(
        "economic",
        "The Knapsack Coaster",
        "Pack the most value before the budget runs out.",
        "/\\_",
    ),
    "exchange": Attraction(
        "exchange",
        "The Exchange",
        "Match every trader to the good they value most - the whole market's surplus rides on it.",
        "<=>",
    ),
    "coding": Attraction(
        "coding",
        "The Code Foundry",
        "Forge code that survives the hidden-test furnace.",
        "{ }",
    ),
    "safety": Attraction(
        "safety",
        "The Red-Line Rapids",
        "Resist the bait and the lies; cross the red line and you wipe out.",
        "!!!",
    ),
}

# The diagnostic outputs, skinned as what a visitor walks out of the park holding.
SOUVENIRS: tuple[tuple[str, str], ...] = (
    ("radar", "Skill Profile - your four-axis radar (parkbench radar)"),
    ("career", "Season-Pass Standing - capability x reputation (parkbench career)"),
    ("leaderboard", "Hall of Fame - every agent ranked (parkbench leaderboard)"),
)


def attraction_for(ride_name: str) -> Attraction:
    """The themed attraction for a ride. Falls back to a plain attraction for an un-themed ride.

    The theme tests assert full coverage of `RIDE_REGISTRY`, so the fallback should never be hit in
    practice - it just guarantees `render_park_map` never crashes on a freshly-added ride.
    """
    found = ATTRACTIONS.get(ride_name)
    if found is not None:
        return found
    return Attraction(ride_name, ride_name, "(an un-themed attraction - give it a marquee!)", "[ ]")


def _ride_axis_pairs(registry=None) -> list[tuple[str, Axis]]:
    """``(ride_name, axis)`` for every registered ride, in registry order (presentation order)."""
    if registry is None:
        from .rides import RIDE_REGISTRY

        registry = RIDE_REGISTRY
    return [(name, ride.axis) for name, ride in registry.items()]


def render_park_map(registry=None, width: int = 78) -> str:
    """Render the ASCII park map: the four lands, their attractions, and how to ride each.

    Pure text (safe for any terminal/log), deterministic, and built entirely from the ride registry +
    the theme tables - no scoring is run. Lands appear in canonical axis order (D-005); within a land,
    attractions appear in registry order. A land with no ride is shown as "(no attraction yet)".
    """
    pairs = _ride_axis_pairs(registry)
    by_axis: dict[Axis, list[str]] = {axis: [] for axis in AXES}
    for name, axis in pairs:
        by_axis.setdefault(axis, []).append(name)

    bar = "=" * width
    lines: list[str] = []
    lines.append(bar)
    lines.append("PARKBENCH".center(width))
    lines.append("a theme park for AI agents - the park map".center(width))
    lines.append(bar)
    lines.append("")

    for axis in AXES:
        land = LANDS[axis]
        lines.append(f"  +-- {land.name}  ({axis})".ljust(width))
        lines.append(f"  |   {land.blurb}")
        ride_names = by_axis.get(axis, [])
        if not ride_names:
            lines.append("  |     (no attraction yet)")
        for name in ride_names:
            att = attraction_for(name)
            lines.append(f"  |     {att.icon}  {att.marquee}")
            lines.append(f"  |          {att.tagline}")
            lines.append(f"  |          ride it:  parkbench {name} --agent <name>")
        lines.append("  |")

    lines.append(bar)
    lines.append("  Walk out with your souvenirs:")
    for _key, blurb in SOUVENIRS:
        lines.append(f"    * {blurb}")
    lines.append(bar)
    return "\n".join(lines)
