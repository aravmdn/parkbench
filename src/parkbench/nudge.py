"""Nudge controls for the observe+nudge loop (decision D-021, refined by D-029).

A *nudge* is a human intervention on a run. Two kinds are supported in v1:

  - **Persona swap** — replace the house roster the agent faces with a single chosen
    counterpart (e.g. only `tough`), to probe how the agent fares against it.
  - **Scenario injection** — run a specific, human-supplied scenario instead of the
    seeded suite scenarios.

Either kind makes the run **off-record** (D-029): nudged runs are flagged
`off_record: true` and are EXCLUDED from canonical profiles / aggregation (see
`scoring.build_profile`). An explicit `--off-record` flag can also be set on its own.

This module owns the small registry + spec-parsing so the CLI and suite changes stay
localized. Zero runtime dependencies (D-023).
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from .personas import (
    HOUSE_CAST,
    CooperativePersona,
    FairPersona,
    SlipperyPersona,
    ToughPersona,
)
from .scenario import Scenario

# Persona name -> class. Mirrors HOUSE_CAST; lets a human address a persona by name.
PERSONA_REGISTRY: dict[str, type] = {
    "tough": ToughPersona,
    "fair": FairPersona,
    "cooperative": CooperativePersona,
    "slippery": SlipperyPersona,
}


def persona_class(name: str) -> type:
    """Resolve a persona name to its class, or raise a clear error."""
    try:
        return PERSONA_REGISTRY[name]
    except KeyError:
        raise ValueError(
            f"Unknown persona '{name}'. Choices: {', '.join(sorted(PERSONA_REGISTRY))}"
        ) from None


def parse_scenario_spec(spec: str) -> Scenario:
    """Build a Scenario from an inline JSON spec or a path to a JSON file.

    Accepted JSON shape (weights need not pre-sum to anything — they are not renormalized;
    supply them already balanced if you want each side's max to be 100):

        {
          "issues": ["price", "term", "support"],   # optional; defaults to issue_0..
          "n_levels": 3,
          "weight_a": [60, 25, 15],
          "weight_b": [20, 30, 50],
          "seed": 1234                               # optional, for labeling/log only
        }
    """
    text = spec
    p = Path(spec)
    try:
        if p.exists() and p.is_file():
            text = p.read_text(encoding="utf-8")
    except OSError:
        # Treat as inline JSON if the string can't be probed as a path (e.g. too long).
        text = spec

    try:
        d = json.loads(text)
    except json.JSONDecodeError as e:
        raise ValueError(f"--inject-scenario is not valid JSON (or a JSON file path): {e}") from None

    if not isinstance(d, dict):
        raise ValueError("Injected scenario spec must be a JSON object.")
    for key in ("weight_a", "weight_b"):
        if key not in d:
            raise ValueError(f"Injected scenario spec is missing required field '{key}'.")

    weight_a = tuple(float(x) for x in d["weight_a"])
    weight_b = tuple(float(x) for x in d["weight_b"])
    if len(weight_a) != len(weight_b):
        raise ValueError("weight_a and weight_b must have the same length.")
    n_issues = len(weight_a)
    if n_issues == 0:
        raise ValueError("Injected scenario needs at least one issue.")

    issues = tuple(d["issues"]) if "issues" in d else tuple(f"issue_{i}" for i in range(n_issues))
    if len(issues) != n_issues:
        raise ValueError("'issues' length must match the number of weights.")
    n_levels = int(d.get("n_levels", 3))
    if n_levels < 2:
        raise ValueError("n_levels must be >= 2.")
    seed = d.get("seed")

    return Scenario(
        issues=issues,
        n_levels=n_levels,
        weight_a=weight_a,
        weight_b=weight_b,
        seed=seed,
    )


@dataclass(frozen=True)
class Nudge:
    """The human intervention applied to a run.

    `swap_persona` restricts the roster to one named counterpart; `inject_scenario`
    supplies a single scenario to run instead of the seeded suite scenarios. Any nudge
    (or an explicit force) makes the run off-record.
    """

    swap_persona: str | None = None
    inject_scenario: Scenario | None = None
    force_off_record: bool = False

    @property
    def is_active(self) -> bool:
        return self.swap_persona is not None or self.inject_scenario is not None

    @property
    def off_record(self) -> bool:
        # Swapping or injecting auto-sets off-record; --off-record forces it directly.
        return self.is_active or self.force_off_record

    def roster(self) -> list[type]:
        """The persona classes to face: the swapped one, else the full house cast."""
        if self.swap_persona is not None:
            return [persona_class(self.swap_persona)]
        return list(HOUSE_CAST)
