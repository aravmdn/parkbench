"""The fixed house cast — the standardized counterparties for the negotiation ride.

These four scripted personas (decision D-024) are the reproducibility infrastructure:
because they are deterministic and fixed, a multi-agent ride scores as reliably as a solo
one (decision D-018). Each is the shared ConcederStrategy tuned to a distinct disposition:

  - Tough        — concedes little, holds out for a high share.
  - Fair         — concedes steadily toward a balanced ~50% split.
  - Cooperative  — concedes quickly, happy to find efficient deals.
  - Slippery     — erratic and self-serving; uses noise to behave inconsistently.
"""

from __future__ import annotations

from ..agents.conceder import ConcederStrategy


class ToughPersona(ConcederStrategy):
    def __init__(self) -> None:
        super().__init__(name="tough", start=0.95, end=0.60, noise=0.0)


class FairPersona(ConcederStrategy):
    def __init__(self) -> None:
        super().__init__(name="fair", start=0.80, end=0.50, noise=0.0)


class CooperativePersona(ConcederStrategy):
    def __init__(self) -> None:
        super().__init__(name="cooperative", start=0.65, end=0.35, noise=0.0)


class SlipperyPersona(ConcederStrategy):
    def __init__(self) -> None:
        super().__init__(name="slippery", start=0.90, end=0.55, noise=0.35)


HOUSE_CAST: list[type[ConcederStrategy]] = [
    ToughPersona,
    FairPersona,
    CooperativePersona,
    SlipperyPersona,
]
