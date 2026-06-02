"""Seeded repeated public-goods ("commons") games + an exact response-bound solver (decision D-045).

The commons ride is the project's **second multi-agent ride** and the **second ride on the social
axis** (D-005) — the first time two rides share an axis, which exercises the radar's per-axis mean
(D-037). Where the negotiation ride (D-010) measures *bilateral bargaining*, this one measures
*cooperation under a social dilemma*: can an agent elicit and sustain cooperation from a society of
other agents when free-riding is individually tempting?

The game is a finitely-repeated **public-goods game**. Each of `n_players` players (the test agent A
is player 0; the rest are the deterministic **house cast** — the reproducibility mechanism, D-004)
starts each round with an `endowment` E and chooses a contribution `c ∈ [0, E]` to a common pool. The
pool is multiplied by `multiplier` m and split equally, so each player's round payoff is::

    payoff_i = (E - c_i) + m * (sum_j c_j) / n_players

With ``1 < m < n_players`` this is a genuine social dilemma: the marginal return of one's *own*
contribution is ``m/n < 1`` (so pure self-interest says contribute 0), yet every unit contributed
returns ``m > 1`` to the group — so the welfare optimum is full cooperation. The only thing that
makes cooperation individually worthwhile is that **some house members react to A** (see the cast):
eliciting their cooperation is the social skill the ride scores.

Scoring (objective payoff vs. baselines — D-011/D-019, here a *best/worst response* bracket): A's play
is scored against the exact best and worst total payoff achievable **against this fixed,
deterministic cast**, both found by brute force over a small discretized strategy space::

    score = (achieved - worst_response) / (best_response - worst_response)   clamped to [0, 1]

so the best response scores 1.0 by construction and the worst scores 0.0. Because the cast is fixed
and deterministic, the bracket is exact and gaming-resistant. Everything is seed-derived: same seed ⇒
byte-identical game ⇒ identical scores.
"""

from __future__ import annotations

import itertools
import random
from dataclasses import dataclass
from typing import Callable

# --------------------------------------------------------------------------------------------------
# House cast — deterministic strategies (D-004: the cast is *scoring infrastructure*, not flavor).
#
# Each member is a pure function of the round index and **A's** past contributions (the test agent is
# the subject of the ride, so the reactive member conditions on A — this is what makes A's social
# skill the clean, sole lever and keeps the best response exactly computable). They never see their
# own or each other's history, which is all they need for the strategies below.
# --------------------------------------------------------------------------------------------------

# A house strategy: (round_idx, a_past_contributions, scenario) -> contribution this round.
HouseStrategy = Callable[[int, tuple[int, ...], "CommonsScenario"], int]


def _cooperator(round_idx: int, a_past: tuple[int, ...], sc: "CommonsScenario") -> int:
    """Unconditional cooperator: always contributes its full endowment."""
    return sc.endowment


def _defector(round_idx: int, a_past: tuple[int, ...], sc: "CommonsScenario") -> int:
    """Unconditional free-rider: never contributes (a constant drag — full cooperation isn't free)."""
    return 0


def _reciprocator(round_idx: int, a_past: tuple[int, ...], sc: "CommonsScenario") -> int:
    """Conditional cooperator with a **grim trigger** on A.

    Contributes its full endowment as long as A has met the cooperation bar (contributed at least
    ``scenario.threshold``) in **every** prior round; the first time A drops below the bar it defects
    (contributes 0) for the rest of the game. Round 0 it cooperates (benefit of the doubt). This is
    the strategic lever: cooperating with it pays (it keeps the pool high), defecting on it is
    permanently punished — so the best response is non-trivial.
    """
    if all(c >= sc.threshold for c in a_past):
        return sc.endowment
    return 0


HOUSE_STRATEGIES: dict[str, HouseStrategy] = {
    "cooperator": _cooperator,
    "reciprocator": _reciprocator,
    "defector": _defector,
}

# The fixed house society: a mix of an unconditional cooperator, a grim-trigger reciprocator (the
# lever), and an unconditional defector. n_players = 4 (A + these three).
DEFAULT_CAST: tuple[str, ...] = ("cooperator", "reciprocator", "defector")


@dataclass(frozen=True)
class CommonsScenario:
    """One finitely-repeated public-goods game (D-045).

    `cast` names the house members (length ``n_players - 1``); A is player 0. `multiplier` satisfies
    ``1 < m < n_players`` so the game is a true social dilemma. The instance is fully seed-derived.
    """

    n_players: int
    n_rounds: int
    endowment: int
    multiplier: float
    cast: tuple[str, ...] = DEFAULT_CAST
    seed: int | None = None

    @property
    def threshold(self) -> int:
        """The cooperation bar the reciprocator watches: half the endowment (E even ⇒ integer)."""
        return self.endowment // 2

    @property
    def levels(self) -> tuple[int, ...]:
        """The discretized contribution choices {none, half, full} used by the exact solver.

        A real agent may contribute *any* integer in ``[0, E]``; these three levels define the
        reference bracket (best/worst response) that scores it. They are deliberately coarse so the
        exact bracket is instant to brute-force (``3 ** n_rounds``), and they include the cooperation
        bar (``half``) so the reciprocator can be exactly satisfied.
        """
        return (0, self.endowment // 2, self.endowment)


@dataclass(frozen=True)
class RoundOutcome:
    """The per-round record of a play-through (for inspection / replay)."""

    contributions: tuple[int, ...]  # one per player, A first
    pool: int
    payoff_a: float


# Defaults: small enough that the exact bracket (3 ** n_rounds, ≤ 3**7 = 2187) and forward simulation
# are instant; an even endowment so the half-level and threshold are integers.
ENDOWMENTS = (8, 10, 12)
ROUND_COUNTS = (5, 6, 7)
MULTIPLIERS = (2.0, 2.5, 3.0)  # all satisfy 1 < m < n_players (=4): a genuine social dilemma


def generate_scenario(seed: int, cast: tuple[str, ...] = DEFAULT_CAST) -> CommonsScenario:
    """Deterministically generate a public-goods game from a seed.

    Varies the endowment, round count, and multiplier per seed (the cast *types* stay fixed — the
    house is the reproducibility mechanism, D-004), so a suite of consecutive seeds spans a range of
    dilemma intensities. Same seed ⇒ byte-identical game.
    """
    rng = random.Random(seed)
    endowment = rng.choice(ENDOWMENTS)
    n_rounds = rng.choice(ROUND_COUNTS)
    multiplier = rng.choice(MULTIPLIERS)
    return CommonsScenario(
        n_players=1 + len(cast),
        n_rounds=n_rounds,
        endowment=endowment,
        multiplier=multiplier,
        cast=cast,
        seed=seed,
    )


# A policy for player A: (round_idx, history) -> contribution. `history` is the list of past rounds'
# full contribution tuples (player 0 = A), so a reactive agent can condition on what the society did.
APolicy = Callable[[int, list[tuple[int, ...]]], int]


def simulate(scenario: CommonsScenario, a_policy: APolicy) -> tuple[float, list[RoundOutcome]]:
    """Play the game forward with A driven by `a_policy`; return A's total payoff + per-round detail.

    A's contribution is clamped to ``[0, E]`` (a malformed/out-of-range contribution is coerced, not
    rewarded). The house members react only to A's past contributions (see the cast). Deterministic
    for a deterministic policy.
    """
    history: list[tuple[int, ...]] = []
    a_past: list[int] = []
    a_total = 0.0
    detail: list[RoundOutcome] = []
    for r in range(scenario.n_rounds):
        try:
            c_a = int(a_policy(r, history))
        except (TypeError, ValueError):
            c_a = 0
        c_a = max(0, min(scenario.endowment, c_a))
        house = tuple(HOUSE_STRATEGIES[name](r, tuple(a_past), scenario) for name in scenario.cast)
        contributions = (c_a,) + house
        pool = sum(contributions)
        payoff_a = (scenario.endowment - c_a) + scenario.multiplier * pool / scenario.n_players
        a_total += payoff_a
        history.append(contributions)
        a_past.append(c_a)
        detail.append(RoundOutcome(contributions=contributions, pool=pool, payoff_a=payoff_a))
    return a_total, detail


def _sequence_policy(seq: tuple[int, ...]) -> APolicy:
    """Wrap a fixed contribution sequence as an (open-loop) A policy."""
    return lambda r, _history: seq[r]


@dataclass(frozen=True)
class ResponseBounds:
    """The exact best/worst total payoff A can achieve against the fixed cast (the scoring bracket)."""

    best: float
    worst: float
    best_sequence: tuple[int, ...]


def solve_response_bounds(scenario: CommonsScenario) -> ResponseBounds:
    """Brute-force the exact best and worst response over the discretized strategy space.

    Enumerates every contribution sequence in ``levels ** n_rounds`` (≤ 2187), simulates each against
    the deterministic cast, and returns the max/min total payoff (and an argmax sequence — the open-
    loop best response the ``optimal`` baseline replays). Ties on the best break to the lexicographically
    smallest sequence for determinism.
    """
    best = float("-inf")
    worst = float("inf")
    best_seq: tuple[int, ...] = ()
    for seq in itertools.product(scenario.levels, repeat=scenario.n_rounds):
        total, _ = simulate(scenario, _sequence_policy(seq))
        if total > best:
            best, best_seq = total, seq
        if total < worst:
            worst = total
    return ResponseBounds(best=best, worst=worst, best_sequence=best_seq)


def score_total(scenario: CommonsScenario, achieved: float, bounds: ResponseBounds | None = None) -> float:
    """Normalize an achieved total payoff onto ``[0, 1]`` against the best/worst-response bracket.

    ``score = (achieved - worst) / (best - worst)``, clamped to ``[0, 1]`` (a non-discretized play
    that beats the discretized best simply caps at 1.0). If the bracket is degenerate (best == worst,
    i.e. no strategic variation), any play is optimal ⇒ 1.0.
    """
    if bounds is None:
        bounds = solve_response_bounds(scenario)
    spread = bounds.best - bounds.worst
    if spread <= 0:
        return 1.0
    return max(0.0, min(1.0, (achieved - bounds.worst) / spread))


def score_policy(scenario: CommonsScenario, a_policy: APolicy, bounds: ResponseBounds | None = None) -> float:
    """Convenience: simulate `a_policy` and score the resulting total payoff."""
    achieved, _ = simulate(scenario, a_policy)
    return score_total(scenario, achieved, bounds)
