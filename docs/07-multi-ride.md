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

_Slice in progress (`feat/radar`) — this section is filled in by that work._

## Agent identity & versioning (D-038)

So results stay **attributable and reproducible over time**, every agent now has a stable identity
(`src/parkbench/agents/base.py`):

- **`Agent.identity() -> AgentIdentity{name, version, config_hash}`** — `name` is the agent's name;
  `version` defaults to the package version (`parkbench.__version__`, falling back to `"0"`);
  `config_hash` is a short (12 hex chars) **deterministic** SHA-256 of the agent's *defining* config.
- **`Agent.config() -> dict`** — the new hook each agent overrides to declare the params that
  distinguish its behaviour (default `{}`). `ConcederStrategy` returns `{start, end, noise}`;
  `LLMAgent` returns `{model}`. The per-match RNG seed is state, not config (excluded); the API key
  is a secret (never hashed).
- **Deterministic by construction:** the hash is taken over a canonical, key-sorted JSON encoding,
  so the *same agent + same code ⇒ the same identity* across instances and processes — no memory
  addresses, no object ids.
- **Backward compatible:** `config()`/`identity()` ship with sensible defaults, so every existing
  agent constructs and runs unchanged.

The identity is **stamped into the run log** as a top-level `agent` block `{name, version,
config_hash}`; the run-log `schema_version` bumps **2 → 3** (additive — see the schema notes in
[`06-v1-architecture.md`](06-v1-architecture.md)). `write_run` gained an optional `agent=` param;
when omitted the block is still emitted, derived from the profile's agent name (version `"0"`), so
older call sites keep working. This is the foundation a future leaderboard / cross-run comparison
keys on.

## Still open

Anti-gaming / reward-hacking safeguards across rides remain an open question
([`04-open-questions.md`](04-open-questions.md)).
