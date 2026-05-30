# 04 — Open Questions

**Status:** Living · **Last updated:** 2026-05-30

Questions still genuinely open. When one is resolved it becomes an entry in the decision log
([`02-decisions.md`](02-decisions.md)) and is listed under "Resolved" below.

_All four v1 follow-ups deferred from the core build (D-026) have now shipped — see **Resolved**
below (D-027–D-030)._

## Open — cross-cutting (post-v1)

- How per-ride scores roll up into the radar profile (weighting, normalization across dissimilar
  rides).
- Anti-gaming / reward-hacking safeguards as more ride types are added.

## Resolved

- **2026-05-30** — **HTTP/JSON server** for external BYO agents built as **D-027** (park-hosted,
  agent-polled, stdlib only; reuses the protocol/engine/runlog unchanged). It realises the wire
  connection D-015 deferred from the core build (D-026). Design in
  [`06-v1-architecture.md`](06-v1-architecture.md).
- **2026-05-30** — **Nudge controls** implemented as **D-029**: persona swap / scenario injection,
  flagged off-record and excluded from canonical profiles; run-log schema versioned with an
  `off_record` flag. See [`06-v1-architecture.md`](06-v1-architecture.md).
- **2026-05-29** — Core v1 ride design locked as **D-015–D-021**.
- **2026-05-29** — Implementation choices locked as **D-023–D-026** (stack, scripted cast, deferred
  LLM, core-only build). The three former v1 ride details are now decided:
  - *Preference generation* → seeded additive utilities with anti-correlated weights
    (D-016; see [`06-v1-architecture.md`](06-v1-architecture.md)).
  - *Round cap* → 8 exchanges per side (D-017).
  - *Persona prompts* → replaced by scripted strategies (D-024).
- **2026-05-30** — Static replay viewer built as **D-028**: `viewer/index.html` (single file,
  no build step, no dependencies). Renders suite header, agent profile, per-persona bars,
  match list, and per-match transcript playback with running score. Sample fixture at
  `viewer/sample-run.json`.
- **2026-05-30** — **LLM provider** wiring resolved as **D-030**: a real LLM reference agent
  (`agents/llm.py`) via OpenRouter's OpenAI-compatible API using stdlib only (no SDK, no new
  runtime dep), with graceful heuristic fallback. Registered as the `llm` CLI agent.
- **2026-05-30** — Ride-refinement questions resolved: **D-031** (per-persona reservation floors →
  crisp, non-overlapping per-persona spread) and **D-032** (suite varies scenario shapes 3–5 × 3–5 +
  moderately dispersed weights). See [`06-v1-architecture.md`](06-v1-architecture.md).
- **2026-05-30** — **Identity & versioning of submitted agents** resolved as **D-038**: every agent
  has a stable `identity()` → `AgentIdentity{name, version, config_hash}` (deterministic short hash
  of the agent's defining config), stamped into the run log as a top-level `agent` block; run-log
  `schema_version` bumped 2 → 3 (additive). Makes results attributable and reproducible over time.
  See [`07-multi-ride.md`](07-multi-ride.md) and [`06-v1-architecture.md`](06-v1-architecture.md).
