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

## Current status (2026-07-08)

**Trust track — convergent/discriminant validity landed (D-057).** The validity harness now also
answers the MTMM question *"are the four radar axes four distinct constructs, or one measured four
times?"* `parkbench validity` emits a **ride × ride Spearman matrix** over the shared roster
`{random, greedy, heuristic}` (N=3 — the set scorable on *every* ride, since negotiation has no
`optimal`): the two **social** rides (negotiation, commons) **converge** (ρ = +1.00 — both punish the
free-rider `greedy`) and that same-axis correlation **strictly exceeds** every social-vs-other-axis
correlation (+0.50) ⇒ **discriminant PASS** (Campbell-Fiske, scoped to the social pair's row/column).
Purely additive measurement — **195 passing tests** (+6); baselines byte-identical. Honest limits kept
in `docs/12-validity.md`: N is tiny, only the social axis has a within-axis pair today (economic×safety
also ties at +1.00 — the visible signature of single-ride axes), and the matrix stabilizes only at ≥8
seeds. A real down-payment on convergent/criterion validity, not proof.

**Trust track — the validity harness landed (D-055).** The project's central claim — that a ride's
score *measures the capability it is named for* (**construct validity**) — is now a **measurement**,
not an assertion. New stdlib module `src/parkbench/validity.py` + `parkbench validity` +
`tests/test_validity.py` validate each ride against a **known-ability ε-optimal ladder** (an agent
that plays the ride's own `optimal` baseline with probability `p`, else `random`, for `p` = 0→1, so
true ability is a dial we set): a ride is valid iff its score rises monotonically with `p`. Reports
Spearman ρ / Kendall τ, monotonic fraction, discrimination index, linearity R², resolvable rungs, and
split-half reliability, plus sanity guards (optimal reaches ~1.0; a high random floor is flagged) and
a formal **gaming-resistance** check (the reward-hacker `greedy` must be *caught* by the career's
reputation weighting — it lands **below random**; Goodhart gap 0.836). Evidence runs on a **held-out
eval seed range** (`EVAL_SEED_BASE = 4000…`, disjoint from the seed-1 public fixtures — a contamination
down-payment). Results (held-out seeds 4000–4011, 6-rung ladder): **all three fast rides VALID** —
economic ρ 1.00 (honest finding: floor 0.71 → *narrow* discrimination 0.29), safety ρ 1.00 (disc
0.70), commons ρ 1.00 (disc 0.52). New doc `docs/12-validity.md` documents the method, thresholds,
results, and the **honest remaining gaps** (convergent/criterion validity, a discriminant MTMM matrix
across the four axes, input-ablation shortcut baselines, a structural capability-limited ladder, item
hygiene, bootstrap CIs, benchmark versioning). **189 passing tests** (the validity harness added +12
from 174 → 186; the later LLM no-key-fallback tests → 189); **baselines
byte-identical** (purely additive — no ride/scoring/agent code touched). Three research passes
(psychometric validity · LLM-benchmark trust/contamination · anti-gaming/Goodhart) converged on this
exact playbook. Verify: `parkbench validity` (~1–2 min), `parkbench validity --json`, `parkbench
validity --coding` (adds the slow subprocess-graded coding ride), `pytest tests/test_validity.py`.
This is roadmap **#6 (the trust track)** — the highest-leverage work for credibility, above more rides
or art. Construct validity remains the project's **central open risk**
(`docs/04-open-questions.md`): the down-payment shows the instrument isn't measuring *noise* and can't
be *gamed* — necessary, not yet sufficient.

**Visual world — all six seed laps landed (D-053).** The Pokémon-style front-end
(`docs/11-visual-world.md`) is now a living little world: a separate **`web/`** app on **Kaplay + Vite**
(deps + build step allowed; the stdlib-only rule is engine-only). All six seed backlog tasks are done —
**web-scaffold** (bootable canvas + `web/README.md`), **overworld-tilemap** (a 20×18 tile park —
grass/path/water/tree), **four-lands** (the four axes as accent-tinted, labeled quadrants: Society
Square · Market Midway · Maker's Workshop · Safety Gauntlet), **gym-buildings** (one gym per scored ride
in its land), **trainer-sprite** (a 4-direction walk-cycle trainer that arrow-key-walks + auto-patrols
the paths), and **wire-radar-json** (a **stats screen** reachable with `S` that renders an agent's
four-axis radar from verbatim `parkbench radar --json` fixtures — heuristic/greedy/optimal/random,
cycled with ← →). All placeholder art is **procedurally generated** in `web/src/pixels.js` (original/CC0
by construction, deterministic), and `web/src/theme.js` mirrors the engine's park vocabulary — the
front-end stays **presentation-only** (D-012), and no engine code changed (Tier A untouched: still
**174 passing tests**). Verify: `cd web && npm install && npm run build`, then `npm run dev` (or
`npm run preview`) and open the served page (walk with arrows, `S` for the radar, `H` for the Hall of
Fame). Tier-B screenshots for each lap are under `autoloop/shots/`.

**Chunk 2 started + the hourly autoloop is designed (D-054).** The **hourly cloud-cron build loop** is
**documented + ready to arm** (`docs/10-autoloop.md` cloud-cron mode; standing prompt in
`autoloop/ROUTINE_PROMPT.md`) — a fresh worker fires each hour, works one `autoloop/backlog.md` task,
verifies (Tier A `pytest` / Tier B `web/` build + headless screenshots), pushes to branch
`claude/next-tasks-j7f20o` + keeps **PR #13** updated (never to `main`), and hands off via
`autoloop/HANDOFF.md`. Viable in the cloud because the remote env ships **Chromium + Playwright** for
Tier-B screenshots (revising D-051's cloud-cron retirement). **Not yet armed:** creating the durable
trigger is blocked on an owner approval of the scheduling MCP call — arm it from claude.ai/code/routines
(or a session where the approval clears) using `autoloop/ROUTINE_PROMPT.md`. **Visual-world chunk 2 is
complete** (PR #13 merged to `main`; follow-up chunk-2 laps on a fresh `claude/next-tasks-j7f20o` → a new
PR): the **Hall of Fame** (`web/src/halloffame.js`, `H`) rendering the ranked career leaderboard from
`leaderboard --json` (optimal 1.000 > heuristic 0.567 > random 0.154 > greedy 0.148); **badge-reputation**
(the stats screen gains earned/cracked/skipped gym-badges + reputation from the leaderboard legs);
**enter-gym-run** (the trainer carries an agent identity; stepping onto a gym plays "NOW RIDING" → reveals
that ride's real score → returns); and **world-signposts** (crossroads lamps, per-land benches, a
"PARKBENCH" entrance sign, a bottom controls legend). **Next:** decompose the next chunk into the backlog
(live/served profiles instead of fixtures; multiple trainers on-screen; a BYO-agent connector). Kill
switch: disable/delete the routine at claude.ai/code/routines.

**Active driver = the local `/loop` loop (D-056, 2026-07-08).** The owner activated the **local driver
(D-051 model)** as the running autoloop; its standing driver/worker prompt is `autoloop/LOCAL_DRIVER_PROMPT.md`
(a thin `/loop` driver spawns one fresh worker subagent per lap; laps work `autoloop/task-<slug>` and land
on `main` gate-free). The **cloud-cron routine (D-054) stays documented but unarmed**. `convergent-validity`
has since landed (D-057); the baton's next trust-track task is **`ablation-baseline`** (roadmap #6, Tier A).
Kill switch: stop the `/loop` session.

---

## Prior status (2026-07-02)

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
timeout. Reproducible: **195 passing tests**. Design + formulas: `docs/06-v1-architecture.md`,
`docs/07-multi-ride.md`, `docs/08-theming.md`, and `docs/09-byo-protocol.md`.

> **⚠️ Superseded by D-054 — see the 2026-07-05 block above.** The autoloop is now an **hourly
> cloud-cron** worker that pushes to branch `claude/next-tasks-j7f20o` + an open PR — **never to
> `main`** — and the cloud cron is **no longer retired**. The paragraph below is kept as the
> D-049/D-051/D-052 historical record; the local `/loop`→`main` model it describes is *not* the current
> mechanism.

**As of 2026-07-02** the project is set up to run an **autonomous build loop** (D-049, re-scoped by
D-051) — governed by the charter `docs/10-autoloop.md`. It runs **locally, one fresh worker sub-session
per lap** (a thin `/loop` driver dispatches each lap to a clean-context worker, so no session fills up,
and it can drive the browser). It **genuinely builds forward** — engine features, new rides, and the new
headline goal: the **Pokémon-style visual world** (D-050, `docs/11-visual-world.md`) — a separate `web/`
front-end app (Kaplay, deps allowed) rendering the stdlib-only engine's JSON. The charter has **two
verification tiers**: engine work must keep `pytest` green + baselines byte-identical; visual work must
build clean **and commit screenshots** to `autoloop/shots/<ts>/` for async review. It is **crash/quota-
safe via a write-ahead handoff baton** (D-052): `autoloop/HANDOFF.md` (live state + `NEXT ACTION`,
updated after every step), `autoloop/backlog.md` (session-sized tasks), `autoloop/log.md` (history) —
each session works **one task to completion** on a per-task branch with WIP commits, resumes a cut-off
task from the baton, and only lands *completed + verified* work on `main` (gate-free). **No PR gate**
(owner's choice). The old cloud cron routine is **retired/disabled**. If you are a session landing here:
**read `docs/10-autoloop.md` + `docs/11-visual-world.md`, then `autoloop/HANDOFF.md`, and reconcile with
`git status` before doing anything.** Kill switch: stop the local `/loop` session (and optionally delete
the disabled cloud routine at claude.ai/code/routines).

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
- **Verify:** `uv venv && uv pip install -e ".[dev]"`, then `pytest` (195 pass; the coding + validity
  tests spawn subprocesses, so the suite takes ~3–4 min),
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
