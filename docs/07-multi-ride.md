# 07 — Multi-ride & the radar profile

**Status:** Living · **Last updated:** 2026-05-30

The post-v1 phase (decision **D-034**). v1 proved one ride can be scored reproducibly; this phase
delivers the project's headline output — the **diagnostic radar profile across skill axes** (D-007)
— which needs **≥2 rides on different axes**. See the roadmap ([`03-roadmap.md`](03-roadmap.md) #1).

## The ride abstraction (D-035)

A *ride* is a self-contained, scored capability test (D-002) that stays independent of the others
(D-008). The contract (`src/parkbench/axis.py`, `src/parkbench/rides.py`):

- **`Axis`** — one of the four skill families (D-005): `social` · `economic` · `coding` · `safety`.
- **`RideResult{ride, axis, agent, score, detail}`** — `score` is the ride's headline metric
  **normalized to `[0, 1]`** (1 = optimal), so dissimilar rides roll up onto one radar; `detail`
  holds the ride-specific breakdown.
- **`Ride`** protocol — `name`, `axis`, and `evaluate(agent_name, seed) -> RideResult`.
- **`RIDE_REGISTRY`** — the rides available for roll-up. New rides register here.

The negotiation ride (D-010) is wrapped as `NegotiationRide` (axis `social`); its normalized score is
mean efficiency. This wrapper is **additive** — the original `parkbench run` path is unchanged.

Each ride defines its own agent interface and ships its own baseline agents; the radar aggregates
whatever ride results exist for an agent.

## Economic ride (D-036)

_Slice in progress (`feat/economic-ride`) — this section is filled in by that work._

## Radar roll-up (D-037)

The headline output (D-007). `src/parkbench/radar.py` turns the independent rides into one
diagnostic profile:

- **`build_radar(agent_name, seed=1, rides=None)`** iterates the rides (default `RIDE_REGISTRY`;
  `rides=` is injectable for testing — accepts a registry-like mapping or any iterable of `Ride`s),
  calls each `ride.evaluate(agent_name, seed)`, and aggregates the normalized `[0, 1]`
  `RideResult.score` **per axis (D-005) by simple mean** where several rides share an axis.
- **`RadarProfile{agent, seed, axis_scores, results, skipped}`** (frozen) is the result.
  `axis_scores` holds only the **covered** axes; an axis with no ride is **absent** and shown as
  `n/a` (a coverage gap, not a 0). `covered_axes` / `missing_axes` partition the four axes in
  canonical order.
- **Graceful skip:** a ride that can't score the agent — its roster has no entry, so `evaluate`
  raises `KeyError`/`ValueError` (D-035: each ride owns its roster) — is skipped and named in
  `skipped`, so a partially-covered agent never crashes the roll-up.
- **Rendering:** `to_dict()` gives a JSON view (stable key order); `render_radar()` draws a compact
  per-axis ASCII bar chart — **stdlib only, no plotting dependency** (D-023).
- **CLI:** `parkbench radar --agent <name> --seed 1 [--json]`.

Deterministic: rides are visited in registry/iteration order and a fixed `seed` yields identical
output. Until the economic ride lands, only the **social** axis (from `NegotiationRide`) populates;
the other three show `n/a`. Rationale and rejected alternatives: **D-037** in
[`02-decisions.md`](02-decisions.md).

## Agent identity & versioning (D-038)

_Slice in progress (`feat/agent-identity`) — this section is filled in by that work._

## Still open

Anti-gaming / reward-hacking safeguards across rides remain an open question
([`04-open-questions.md`](04-open-questions.md)).
