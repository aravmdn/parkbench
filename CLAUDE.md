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

## Current status (2026-07-02)

**v1 + the post-v1 multi-ride phase are on `main`; the four-axis diagnostic radar is complete.** The
negotiation ride runs end-to-end: engine, seeded scenario generator, objective-payoff scoring,
scripted house cast, baseline/heuristic agents, and a `parkbench` CLI — plus the **HTTP/JSON server**
for external BYO agents (D-027), a **static replay viewer** (D-028), **nudge controls** with
off-record flagging (D-029), a real **LLM reference agent** via OpenRouter (D-030), tuned personas +
a varied scenario suite (D-031/D-032), and `.env` auto-load (D-033). The **multi-ride phase** then
added a ride abstraction (D-034/D-035), the **radar roll-up** (D-037), **agent identity/versioning**
in run logs (D-038), and **all four scored rides**: negotiation (social, D-010), a **solo Economic
knapsack ride** (D-036), a **solo Coding code-generation ride** (D-039, hidden-test scored with
seed-randomized tests), and a **solo Safety red-line ride** (D-040, an adversarial reward-hacking
probe). The phase then landed the **first cross-ride coupling**: a **career** (D-041) — reputation
that compounds across rides — and a **leaderboard** (D-042). The coding harness is **sandboxed +
time-bounded** (D-043, subprocess + wall-clock timeout), and a static zero-dependency
**diagnostic-profile viewer** renders the radar/career/leaderboard (D-044, `viewer/profiles.html`).
The park gained a **fifth ride — a multi-agent Commons public-goods ride** (D-045), the **second ride
on the social axis**, so the radar's per-axis mean is now exercised by two real rides (social =
mean(negotiation, commons)). The **creative skin** landed (D-046, roadmap #4): a presentation-only
`theme.py` (lands = axes, attractions = rides), a `parkbench map` command, and a third static
zero-dependency page `viewer/park.html` (the themed entrance). Most recently, on the **BYO/hardening
track (roadmap #5)**: the HTTP/JSON wire protocol is now **documented as a language-agnostic spec**
(D-047, `docs/09-byo-protocol.md`), and the coding sandbox gained **environment + working-directory
confinement** (D-048, no inherited secrets, throwaway cwd) on top of its D-043 process isolation +
timeout. Reproducible: **174 passing tests**. Design + formulas: `docs/06-v1-architecture.md`,
`docs/07-multi-ride.md`, `docs/08-theming.md`, and `docs/09-byo-protocol.md`.

**As of 2026-07-02** the project also runs an **autonomous self-development loop** (D-049): a scheduled
agent runs one **lap** ~every 5 h, unattended, governed by the charter `docs/10-autoloop.md`. A lap
picks one item from the queue (broken things → `04-open-questions.md` → `03-roadmap.md` → the *Next*
bullets below), implements it, keeps the suite green + baselines byte-identical, syncs docs + decision
log + this status, and **pushes to `main` only if the suite is green and the item is complete** (else it
parks WIP on an `autoloop/wip-*` branch — `main` is never left red). **No PR gate** (owner's choice). If
you are a session (human or agent) landing here: **read `docs/10-autoloop.md` before running a lap.**
Kill switch: `/schedule` → disable/delete the Parkbench autoloop routine.

- **Headline:** the radar for `heuristic` spans **all four** axes — **social 0.963** (mean of
  negotiation 0.975 + commons 0.951) + **economic 0.990** (knapsack) + **coding 0.667**
  (code-generation) + **safety 0.667** (red-line). The **career (D-041)** turns that into one
  cross-ride number: `career_score = mean_capability × reputation`, where **reputation = the product
  of each ride's `integrity` signal** (safety non-violation · economic feasibility · coding compile ·
  social neutral). It makes a reward-hacker pay — seed 1 leaderboard: **optimal 1.000 > heuristic
  0.567 > random 0.154 > greedy 0.148**, i.e. `greedy` (the economic *star* at 0.989) lands **dead
  last, below `random`**, because its 67 % red-line violation rate collapses its reputation to 0.333
  (and since D-045 it is *also* the worst social baseline). Per-ride (seed 1): commons optimal 1.000 >
  heuristic 0.951 > random 0.492 > greedy 0.469 (free-rider punished by reciprocity); safety optimal
  1.000 > heuristic 0.667 > greedy 0.333 > random 0.276; coding optimal 1.000 > heuristic 0.667 >
  greedy 0.333 > random 0.000; negotiation efficiency heuristic 0.975 > random 0.881 > greedy 0.100.
- **Next** (`docs/03-roadmap.md`, `docs/04-open-questions.md`): roadmap **#3 (career) is done** and
  **#4 (spectator product) is well underway** — `leaderboard` (D-042), the `profiles.html` viewer
  (D-044), and now the **creative skin** (D-046, `parkbench map` + `viewer/park.html`); remaining #4
  is richer per-ride art and possibly live/served profiles. **#5 (BYO ecosystem)**: the wire protocol
  is now **documented** (D-047) and the coding harness is sandboxed + **env/cwd-confined** (D-043 +
  D-048); next is protocol *hardening* for public hosting (auth/TLS/rate limiting + a JSON Schema), BYO
  connectors for the solo rides, and a **full OS sandbox** (network/abs-path/resource confinement) for
  untrusted code — the one anti-gaming item still open. LLM house personas remain a fast-follow (D-024).
- **Verify:** `uv venv && uv pip install -e ".[dev]"`, then `pytest` (174 pass; the coding tests
  spawn subprocesses, so the suite now takes ~40s),
  `parkbench map` (the themed park map), `parkbench run --agent heuristic --seed 1`,
  `parkbench economic --agent greedy`, `parkbench coding --agent heuristic`,
  `parkbench safety --agent heuristic`, `parkbench commons --agent optimal` (the multi-agent
  public-goods ride), `parkbench radar --agent heuristic` (4-axis profile),
  `parkbench career --agent greedy` (the reward-hacker's reputation collapse), and
  `parkbench leaderboard` (the ranked board). Spectator viewers:
  `python -m http.server 8080 --directory viewer/` then open `/park.html` (the entrance) or
  `/profiles.html` (or open the files directly). Live LLM: set `OPENROUTER_API_KEY` (+ optional
  `OPENROUTER_MODEL`), then `parkbench run --agent llm --seed 1`.

## Conventions for growing the docs

- New docs are numbered (`06-…`, `07-…`) and added to the table in `docs/README.md`.
- One topic per file; keep each file scannable.
- Cross-link between docs rather than duplicating content.
- When a doc supersedes part of another, note it explicitly and update the decision log.
