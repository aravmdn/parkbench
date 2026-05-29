# Documentation — Parkbench

This folder is the **source of truth** for Parkbench (a theme park / benchmark arena for AI agents).
Anyone (human or agent) working on the project should read the relevant docs here before acting, and
keep them updated as things change. See the root [`../CLAUDE.md`](../CLAUDE.md) for the operating rules.

## How to use these docs

- **New here?** Read `00-vision.md` first, then `01-v1-scope.md`.
- **Building / reading the code?** See `06-v1-architecture.md`.
- **Making a decision?** Record it in `02-decisions.md`.
- **Hit something undecided?** Park it in `04-open-questions.md`.
- **Unsure what a term means?** Check `05-glossary.md`.

## Index

| # | Doc | Purpose | Status |
|---|---|---|---|
| 00 | [`00-vision.md`](00-vision.md) | What Parkbench is; the strategic thesis; locked decisions. | Stable |
| 01 | [`01-v1-scope.md`](01-v1-scope.md) | The v1 slice — flagship negotiation ride, scoring, success criteria, out-of-scope. | Stable |
| 02 | [`02-decisions.md`](02-decisions.md) | Append-only decision log with rationale. | Living |
| 03 | [`03-roadmap.md`](03-roadmap.md) | Directional roadmap beyond v1. | Living |
| 04 | [`04-open-questions.md`](04-open-questions.md) | Deferred questions to resolve at planning time. | Living |
| 05 | [`05-glossary.md`](05-glossary.md) | Shared vocabulary. | Living |
| 06 | [`06-v1-architecture.md`](06-v1-architecture.md) | How the v1 core is built — modules, scoring formulas, how to run, results. | Stable |

### Reference

- [`reference-survey-2026.md`](reference-survey-2026.md) — the founding research survey *Designing a
  Digital Theme Park for AI Agents (2026)* that seeded the project. **Background only**; deliberately
  open-ended and **not authoritative** for decisions (those live in `02-decisions.md`).

## Convention for adding docs

- Number new docs sequentially (`07-…`, `08-…`) and add a row to the index above.
- One topic per file; keep it scannable; cross-link instead of duplicating.
- Mark each doc's status: **Stable** (settled), **Living** (expected to grow), or **Draft**.
- When a doc changes a prior decision, add an entry to `02-decisions.md`.

## Document history

- **2026-05-29** — Initial docs created from the scope discussion. Project at pre-implementation stage.
- **2026-05-29** — v1 negotiation-ride design decisions locked (D-015–D-021); `01-v1-scope.md` and `04-open-questions.md` updated.
- **2026-05-29** — Project named **Parkbench** (D-022); founding survey moved to `reference-survey-2026.md`; public GitHub repo created.
- **2026-05-29** — v1 core implemented (engine + scoring + CLI); added `06-v1-architecture.md`; decisions D-023–D-026.
