"""The fixed house cast — the standardized counterparties for the negotiation ride.

These four scripted personas (decision D-024) are the reproducibility infrastructure:
because they are deterministic and fixed, a multi-agent ride scores as reliably as a solo
one (decision D-018). Each is the shared ConcederStrategy tuned to a distinct disposition.

Spread discipline (decision D-031). The plain ConcederStrategy accepts any standing offer
that merely beats *its own* current proposal. When the test agent opens generously, that
makes every persona accept the same early offer, so per-persona breakdowns collapse to the
same outcome. To keep the breakdowns crisp, each persona adds an explicit, time-varying
**reservation floor** (a fraction of its own maximum) below which it will NOT accept,
regardless of how the offer compares to its own proposal. A tough persona therefore rejects
a generous opening that a cooperative persona grabs, forcing the negotiation to continue and
produce distinguishable agreements. The floor relaxes from `reserve_start` to `reserve_end`
over the round cap so no persona stonewalls into a needless no-deal.

  - Tough        — high reservation floor, concedes little and late; holds out for a big share.
  - Fair         — moderate floor, concedes steadily toward a balanced ~50% split.
  - Cooperative  — low floor, concedes quickly; happy to find efficient deals fast.
  - Slippery     — high-ish floor with noise; jitters its floor and takes back concessions,
                   so it behaves inconsistently from turn to turn.
"""

from __future__ import annotations

from ..agents.conceder import ConcederStrategy
from ..protocol import Action, Observation


class Persona(ConcederStrategy):
    """A ConcederStrategy with an explicit, time-varying reservation floor.

    `reserve_start` / `reserve_end` are the fraction of the persona's own maximum it
    requires to accept, at the start and end of the match respectively. The floor only
    *gates* acceptance; the underlying ConcederStrategy still decides what to propose.
    Keeping the gate in the persona subclass leaves the shared ConcederStrategy (used by
    the heuristic test agent) untouched.
    """

    def __init__(
        self,
        name: str,
        start: float,
        end: float,
        reserve_start: float,
        reserve_end: float,
        noise: float = 0.0,
    ) -> None:
        super().__init__(name=name, start=start, end=end, noise=noise)
        self.reserve_start = reserve_start
        self.reserve_end = reserve_end

    def _progress(self, obs: Observation) -> float:
        total = max(1, self.total_rounds)
        return min(1.0, max(0.0, (total - obs.rounds_left) / total))

    def _reservation(self, obs: Observation) -> float:
        """The minimum payoff (absolute, in this persona's own units) to accept now."""
        progress = self._progress(obs)
        frac = self.reserve_start - (self.reserve_start - self.reserve_end) * progress
        if self.noise:
            # Slippery jitters its own floor, so its acceptances look inconsistent.
            frac += (self.rng.random() - 0.5) * self.noise
        frac = min(0.99, max(0.0, frac))
        return obs.my_max * frac

    def act(self, obs: Observation) -> Action:
        target = self._target(obs)
        proposal = self._propose(obs, target)
        proposal_value = obs.my_value(proposal)
        standing = obs.standing_offer
        if standing is not None:
            standing_value = obs.my_value(standing)
            reservation = self._reservation(obs)
            # Accept only if the offer clears BOTH the reservation floor and our own
            # proposal — the floor is what distinguishes a tough hold-out from a quick yes.
            if standing_value >= reservation and standing_value >= proposal_value:
                return Action.accept("That works for me — deal.")
            # End-game fallback: don't walk away from a serviceable deal on the last round.
            if obs.rounds_left <= 1 and standing_value >= obs.my_max * self.reserve_end:
                return Action.accept("Fine, let's close on that.")
        return Action.make_offer(proposal, "Here's my proposal.")


class ToughPersona(Persona):
    def __init__(self) -> None:
        super().__init__(
            name="tough", start=0.98, end=0.78,
            reserve_start=0.90, reserve_end=0.72, noise=0.0,
        )


class FairPersona(Persona):
    def __init__(self) -> None:
        super().__init__(
            name="fair", start=0.82, end=0.55,
            reserve_start=0.62, reserve_end=0.48, noise=0.0,
        )


class CooperativePersona(Persona):
    def __init__(self) -> None:
        super().__init__(
            name="cooperative", start=0.50, end=0.22,
            reserve_start=0.28, reserve_end=0.15, noise=0.0,
        )


class SlipperyPersona(Persona):
    def __init__(self) -> None:
        super().__init__(
            name="slippery", start=0.95, end=0.62,
            reserve_start=0.80, reserve_end=0.50, noise=0.45,
        )


HOUSE_CAST: list[type[Persona]] = [
    ToughPersona,
    FairPersona,
    CooperativePersona,
    SlipperyPersona,
]
