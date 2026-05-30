# CLAUDE.md — Parkbench (a theme park for AI agents)

> **READ THIS FIRST, EVERY TIME.** This file is the entry point for any work on this project.
> Before writing code, designing, planning, or answering questions about this project, **read
> `docs/README.md` and the relevant files under `docs/`.** The `docs/` folder is the source of
> truth — this `CLAUDE.md` is only a router to it.

## Operating rules for this project (non-negotiable)

1. **Documentation-first.** Every decision, design, and change must be documented — not only for
   the agent, but for the human owner too. If it isn't written down in `docs/`, it didn't happen.
2. **Always read before acting.** At the start of any task touching this project, read
   `docs/README.md`, then the doc(s) relevant to the task. The doc set **grows incrementally** —
   never assume you remember it; re-check, because new docs may have been added since last time.
3. **Keep docs in sync.** When anything changes (scope, a decision, a design), update the relevant
   doc(s) in the same session, and add a line to the decision log (`docs/02-decisions.md`) when a
   decision is made or reversed.
4. **No silent scope creep.** v1 scope is deliberately narrow (see `docs/01-v1-scope.md`). Anything
   outside it goes to `docs/03-roadmap.md` or `docs/04-open-questions.md`, not into the build.
5. **Leave it resumable.** Before ending a set of tasks, update the **Current status** section below
   (where things stand · what's next · how to verify), ensure decisions are logged and open threads
   are in `docs/04-open-questions.md`, and commit/push so `main` reflects reality. A fresh session
   should be able to resume from `CLAUDE.md` + `docs/` alone.

## What this project is (one-liner)

**Parkbench** is a **modular benchmark arena for AI agents, skinned as a theme park** — each "ride"
is a self-contained, scored test of a capability, and an agent comes out with a **diagnostic skill
profile**. Purpose: become a *trusted, reproducible* place to measure agents. Full framing in
`docs/00-vision.md`.

## Documentation map

| Doc | What's in it |
|---|---|
| `docs/README.md` | Index of all docs + the convention for adding new ones. **Start here.** |
| `docs/00-vision.md` | What this is, the strategic thesis (differentiation), and the locked decisions. |
| `docs/01-v1-scope.md` | The v1 slice: the flagship negotiation ride, scoring, success criteria, out-of-scope. |
| `docs/02-decisions.md` | Decision log (ADR-style) — every decision + rationale, append-only. |
| `docs/03-roadmap.md` | Directional roadmap beyond v1. |
| `docs/04-open-questions.md` | Deferred (often borderline-technical) questions to resolve later. |
| `docs/05-glossary.md` | Shared vocabulary (ride, house cast, BYO agent, radar profile, …). |
| `docs/06-v1-architecture.md` | How the v1 core + follow-ups are built — modules, formulas, how to run, results. |

## Current status (2026-05-30)

**v1 core + all four follow-ups are on `main`** (PRs #1–#7 merged). The negotiation ride runs
end-to-end: engine, seeded scenario generator, objective-payoff scoring, scripted house cast,
baseline/heuristic agents, and a `parkbench` CLI — plus the **HTTP/JSON server** for external BYO
agents (D-027), a **static replay viewer** over the run logs (D-028), **nudge controls** with
off-record flagging (D-029), a real **LLM reference agent** via OpenRouter (D-030), and tuned
personas + a varied scenario suite (D-031/D-032), and `.env` auto-load for the LLM key (D-033).
Reproducible: **57 passing tests**. Design +
formulas: `docs/06-v1-architecture.md`.

- **Headline (seed 1, 48 matches):** efficiency heuristic 0.975 > random 0.881 > greedy 0.100;
  per-persona own-value spreads cooperative 0.772 → fair 0.554 → slippery 0.511 → tough 0.356.
- **Next** (`docs/04-open-questions.md`, now post-v1 cross-cutting): radar roll-up across rides,
  anti-gaming safeguards, agent identity/versioning; LLM house personas remain a fast-follow (D-024).
- **Verify:** `uv venv && uv pip install -e ".[dev]"`, then `pytest` (57 pass) and
  `parkbench run --agent heuristic --seed 1`. Live LLM: set `OPENROUTER_API_KEY` (+ optional
  `OPENROUTER_MODEL`), then `parkbench run --agent llm --seed 1`.

## Conventions for growing the docs

- New docs are numbered (`06-…`, `07-…`) and added to the table in `docs/README.md`.
- One topic per file; keep each file scannable.
- Cross-link between docs rather than duplicating content.
- When a doc supersedes part of another, note it explicitly and update the decision log.
