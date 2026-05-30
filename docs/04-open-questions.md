# 04 — Open Questions

**Status:** Living · **Last updated:** 2026-05-30

Questions still genuinely open. When one is resolved it becomes an entry in the decision log
([`02-decisions.md`](02-decisions.md)) and is listed under "Resolved" below.

## Open — next build (deferred from v1 core, D-026)

- **HTTP/JSON server** so external BYO agents connect over the wire (D-015).
- **Static replay viewer** over the JSON run logs; the log schema's minimum feature set for replay.
- **Nudge** controls (inject scenario / swap persona) + off-record flagging so nudged runs don't
  pollute canonical profiles (D-021).
- **LLM provider** wiring for a real reference agent (implement `Provider.complete` + `LLMAgent.act`)
  (D-025).

## Open — cross-cutting (post-v1)

- How per-ride scores roll up into the radar profile (weighting, normalization across dissimilar
  rides).
- Anti-gaming / reward-hacking safeguards as more ride types are added.
- Identity & versioning of submitted agents (attributable, reproducible results over time).

## Resolved

- **2026-05-29** — Core v1 ride design locked as **D-015–D-021**.
- **2026-05-29** — Implementation choices locked as **D-023–D-026** (stack, scripted cast, deferred
  LLM, core-only build). The three former v1 ride details are now decided:
  - *Preference generation* → seeded additive utilities with anti-correlated weights
    (D-016; see [`06-v1-architecture.md`](06-v1-architecture.md)).
  - *Round cap* → 8 exchanges per side (D-017).
  - *Persona prompts* → replaced by scripted strategies (D-024).
- **2026-05-30** — Ride-refinement questions resolved: **D-031** (per-persona reservation floors →
  crisp, non-overlapping per-persona spread) and **D-032** (suite varies scenario shapes 3–5 × 3–5 +
  moderately dispersed weights). See [`06-v1-architecture.md`](06-v1-architecture.md).
