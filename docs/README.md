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
| 07 | [`07-multi-ride.md`](07-multi-ride.md) | Post-v1: the ride abstraction, the radar roll-up, and added rides. | Living |
| 08 | [`08-theming.md`](08-theming.md) | The creative skin (roadmap #4): the park theme, `parkbench map`, and the landing page. | Living |
| 09 | [`09-byo-protocol.md`](09-byo-protocol.md) | The BYO agent HTTP/JSON wire protocol (roadmap #5) — endpoints, message shapes, determinism. | Living |

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
- **2026-05-30** — v1 follow-ups landed in parallel (PRs #3–#7): HTTP/JSON server (D-027), replay
  viewer (D-028), nudge controls (D-029), LLM reference agent via OpenRouter (D-030), and ride tuning
  (D-031–D-032). 54 passing tests.
- **2026-05-30** — `.env` auto-load added (D-033, 57 tests). Docs synced to the shipped follow-ups:
  refreshed the root README, checked off the `01` success criteria, added a replay-viewer section to
  `06`, new glossary terms in `05`, and cleared the resolved "next build" items from `04`.
- **2026-05-30** — Entered the post-v1 multi-ride phase (D-034): added the ride abstraction (D-035,
  `07-multi-ride.md`) and began the economic ride (D-036), radar roll-up (D-037), and agent
  identity/versioning (D-038).
- **2026-05-30** — Multi-ride phase shipped (PRs #10–#12): the **Economic knapsack ride** (D-036),
  the **radar roll-up** (D-037), and **agent identity/versioning** (D-038) all merged. The radar now
  spans two axes — social 0.975 + economic 0.990 for `heuristic`. 95 passing tests.
- **2026-05-31** — **Coding ride** (D-039) added: a solo, hidden-test-scored code-generation ride on
  the **coding** axis, with seed-randomized tests as a first anti-gaming safeguard. The radar now
  spans **three** axes — social 0.975 + economic 0.990 + coding 0.667 for `heuristic`. 111 passing
  tests. Updated `02`, `03`, `04`, `07`.
- **2026-05-31** — **Safety ride** (D-040) added: a solo "red-line under adversarial pressure" ride on
  the **safety** axis — an explicit reward-hacking probe (crossing a red line scores 0; injections are
  the adversarial nudge). **The radar is now complete across all four axes** — for `heuristic`: social
  0.975 + economic 0.990 + coding 0.667 + safety 0.667. 127 passing tests. Updated `02`, `03`, `04`,
  `07`.
- **2026-05-31** — **Cross-ride career** (D-041) + **leaderboard** (D-042): the first cross-ride
  coupling (roadmap #3). Each ride declares an `integrity` signal; **reputation = the product** of
  them and **`career_score = mean_capability × reputation`**, so misconduct anywhere discounts
  capability everywhere. The reward-hacker `greedy` (economic star) now ranks **last, below `random`**.
  143 passing tests. Updated `02`–`05`, `07`, and root `CLAUDE.md`.
- **2026-05-31** — Two parallel follow-ups (fanned out to sub-agents): the coding harness is now
  **sandboxed + time-bounded** (D-043, subprocess + wall-clock timeout — closes the long-flagged
  untrusted-code gap; baselines byte-identical), and a static zero-dependency **diagnostic-profile
  viewer** (D-044, `viewer/profiles.html`) renders the radar/career/leaderboard outputs (roadmap #4).
  **150 passing tests.** Updated `02`–`05`, `07`, and root `CLAUDE.md`.
- **2026-06-02** — **Commons ride** (D-045): the project's **second multi-agent ride** and **second
  ride on the social axis** — a finitely-repeated public-goods game scored against the exact
  best/worst response to a fixed reactive house cast. It is the first ride to *share an axis*, so the
  radar's per-axis **mean** is now exercised by two real rides (social = mean(negotiation, commons)).
  The free-rider `greedy` is the *worst* baseline, generalizing the reward-hacker story to
  cooperation; the career headline only hardens (seed 1: optimal 1.000 > heuristic 0.567 > random
  0.154 > greedy 0.148). **164 passing tests.** Updated `02`, `03`, `07`, and root `CLAUDE.md`.
- **2026-06-03** — **Park skin** (D-046, roadmap #4): the creative theme applied as a presentation-only
  layer — `src/parkbench/theme.py` (lands = axes, attractions = rides), a `parkbench map` command, and
  a third static zero-dependency page `viewer/park.html` (the themed entrance, links the viewers). New
  doc [`08-theming.md`](08-theming.md). The skin never touches scoring (D-012). **171 passing tests.**
  Updated `02`, `03`, root `CLAUDE.md`, and `viewer/README.md`.
- **2026-06-04** — **BYO protocol spec** (D-047, roadmap #5): documented the HTTP/JSON wire contract
  (endpoints, message shapes, the poll loop, the determinism contract) in new
  [`09-byo-protocol.md`](09-byo-protocol.md) so a third party can implement an agent in any language.
  Docs-only; no code change.
- **2026-06-04** — **Coding sandbox hardening** (D-048): the untrusted-candidate subprocess now also
  gets **environment + working-directory confinement** — a minimal allowlisted env (no inherited
  secrets in `os.environ`) and a throwaway cwd (relative writes can't touch the repo). Baselines
  byte-identical; **174 passing tests.** Updated `02`, `04`, `07`.
