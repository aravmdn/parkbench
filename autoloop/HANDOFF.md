# HANDOFF — the live baton

> The single source of truth for what's happening **right now**. Updated **write-ahead** (after every
> meaningful step, before any long op) — a usage cutoff can kill a session mid-step. **Git is ground
> truth for work done; this file is ground truth for intent / next action.** See
> [`../docs/10-autoloop.md`](../docs/10-autoloop.md) for the protocol.

---

**Updated:** 2026-07-22
**Loop state:** IDLE

**Active task:** — (none; second parallel fan-out batch landed)
**Acceptance criteria:** —
**Task branch:** D-066 + D-067 were merged onto `integration/parallel-laps-2-2026-07-22` (worktree
branches `worktree-agent-a298f2036f67e2181` serve af58744 + `worktree-agent-a2dff5aeac81e0b5c` exchange
c77d4c5; only `cli.py` overlapped — auto-merged), the viewer callout fixed, then **merged into `main` and
pushed to `origin`.**
**Tree state:** clean · on `main`
**Last durable commit:** `git log -1` (the batch-2 consolidation, now on `main`)

**Last integrated (2026-07-22, batch 2):** two parallel laps, merged + verified *together*, **bench →
v1.1.0**:
- **D-066 "The Exchange"** (Tier A, SCORE-ALTERING) — a 2nd economic ride (assignment / Hungarian solver,
  best/worst bracket) makes the economic radar axis `mean(knapsack, exchange)`; repairs the narrow
  economic range (ε-ladder floor 0.71→0.49, disc 0.29→0.51, VALID). `BENCHMARK_VERSION` 1.0.0→1.1.0, all
  8 fixtures regenerated. **Seed-1 leaderboard reorders** (`optimal > heuristic > greedy > random`): the
  reward-hacker `greedy` is no longer dead-last (still caught below `heuristic`; `below_random` holds on
  held-out seeds). MTMM: economic monotrait pair converges (ρ+1.00) but economic-vs-safety discriminant
  **FAILs** (expected; social still PASSes). `viewer/profiles.html` reward-hacker callout fixed to detect
  by collapsed reputation + economic strength (rank-independent).
- **D-067 `serve --profiles`** (Tier A, additive) — stdlib read-only HTTP endpoint
  (`src/parkbench/profiles_server.py`) serving verbatim radar/career/leaderboard `--json`; resolves the
  deferred `docs/04` endpoint. Chunk 4 decomposed into the backlog.
Combined verification: **280 passing tests**, `export-profiles --check` 8 `ok` at v1.1.0, `web/` build
clean. Prior batch: D-063/064/065 (now the first "Prior status" block in `CLAUDE.md`). Per-lap:
[`log.md`](log.md); narrative: root `CLAUDE.md`.

**Loop / active driver (D-056):** the owner-activated local `/loop` driver remains the standing
mechanism (`autoloop/LOCAL_DRIVER_PROMPT.md`). The **cloud-cron routine (D-054) stays DESIGNED +
UNARMED**.

**NEXT ACTION:** Loop is IDLE; D-066/067 are **landed on `main` + pushed**. Open chunk-4 backlog tasks
(pull from the top): **`web-fetch-profiles`** (wire the `web/` app to `fetch` from the new
`serve --profiles` endpoint, fixtures as offline fallback) · **`byo-live-connector`** (render a *live*
BYO run over the `docs/09` wire as the BYO trainer's data) · **`richer-land-art`**. Trust-track next:
per `docs/13`, either give **safety/coding** a 2nd ride too (so their axes get monotrait pairs) or start
the **criterion-validity** cohort (needs a one-time online real-agent step). Loose ends: (a) the
economic-vs-safety **discriminant FAIL** (D-066) wants a richer BYO agent roster to resolve — tracked in
`docs/13`; (b) the Tier-B screenshot of the BYO trainer is still uncaptured (Kaplay canvas-capture was
flaky).

**Blockers / needs-owner:** none. `main` reflects reality (landed + pushed). Optional: the D-065
`llm:<model-id>` agents run **live** only if `.env`'s `OPENROUTER_API_KEY` is valid — present as of
2026-07-22 (not validity-checked); the roster otherwise runs offline via the heuristic fallback.
