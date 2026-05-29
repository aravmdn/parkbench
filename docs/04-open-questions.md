# 04 — Open Questions

**Status:** Living · **Last updated:** 2026-05-29

Questions still genuinely open. When one is resolved it becomes an entry in the decision log
([`02-decisions.md`](02-decisions.md)) and is listed under "Resolved" below.

## Still open — v1 ride details (resolve at implementation/planning)

- **Per-scenario preference generation** — how issue weights are generated/balanced so each scenario
  has a meaningful integrative structure and a well-defined optimum (Pareto/Nash).
- **Persona prompts** — exact wording/behavior specs for the 3–4 house personas (tough / fair /
  cooperative / slippery), plus validation that they behave distinctly and deterministically.
- **Round cap / deadline value** — the actual N, tuned so good agents can reach deals but stalling
  is penalized.

## Still open — observe + nudge

- Exact log schema and the replay viewer's minimum feature set for v1.
- Precisely what a "nudge" can perturb beyond scenario choice + persona swap.

## Still open — cross-cutting (post-v1)

- How per-ride scores roll up into the radar profile (weighting, normalization across dissimilar
  rides).
- Anti-gaming / reward-hacking safeguards as more ride types are added.
- Identity & versioning of submitted agents (attributable, reproducible results over time).

## Resolved

- **2026-05-29** — Core v1 ride design (BYO protocol, negotiation structure, interaction shape, house
  cast, baselines, scoring suite, observe+nudge surface) locked as **D-015–D-021** in
  [`02-decisions.md`](02-decisions.md).
