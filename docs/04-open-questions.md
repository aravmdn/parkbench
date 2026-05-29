# 04 — Open Questions

**Status:** Living · **Last updated:** 2026-05-29

Questions still genuinely open. When one is resolved it becomes an entry in the decision log
([`02-decisions.md`](02-decisions.md)) and is listed under "Resolved" below.

## Open — refine the ride

- **Persona behavioral spread.** Personas differ in aggregate (own-value drops from `cooperative` to
  `tough`), but can collapse to the same outcome on individual scenarios when the test agent's first
  offer is already generous. Tune persona acceptance/proposal so per-persona breakdowns are crisper.
- **Scenario diversity.** Whether 4 issues × 3 levels and the current weight generation give enough
  spread; consider varying issue/level counts across the suite.

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
