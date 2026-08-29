# HANDOFF — the live baton

> The single source of truth for what's happening **right now**. Updated **write-ahead** (after every
> meaningful step, before any long op) — a usage cutoff can kill a session mid-step. **Git is ground
> truth for work done; this file is ground truth for intent / next action.** See
> [`../docs/10-autoloop.md`](../docs/10-autoloop.md) for the protocol.

---

**Updated:** 2026-08-29
**Loop state:** IDLE

**Active task:** — (none; `byo-live-connector` complete, **uncommitted in the working tree**)
**Acceptance criteria:** met — see D-073 in `../docs/02-decisions.md`.
**Task branch:** none — worked directly on `main`, **not yet committed** at the owner's request
(the work is staged to be split into ~5 commits: connector module + tests · `byo-run` CLI · `/byo`
route · `web/` rendering + shots · docs/status).
**Tree state:** DIRTY · on `main` (in sync with `origin/main` at `e3a763e` before this lap)
**Last durable commit:** `e3a763e` (docs: update CLAUDE.md status for D-069..D-072)

**This lap (2026-08-29): `byo-live-connector` — D-073, visual-world chunk 4 COMPLETE.** A live BYO run
over the real `docs/09` wire replaces the hand-authored `radar-byo.json` stand-in in the world:
`src/parkbench/byo.py` (+ `parkbench byo-run`, + a `/byo` route on `serve --profiles`, + `web/`
rendering). A wired leg is byte-identical to the in-process `NegotiationRide` (`detail` included) and
the payload is deterministic (no clock, no port). **Honest outcome:** the v1 wire scores negotiation
only ⇒ a live BYO profile covers **one axis**, so the stats screen now draws uncovered axes as dimmed
**`n/a`** rather than `0.000` — strictly narrower than the fixture it replaces, and that is the point.
`acme-bot` stays correctly absent from the Hall of Fame (a career multiplies integrity across *all*
rides). **369 passing tests** (+23); purely additive — no ride/scoring/fixture/`BENCHMARK_VERSION`
change. Tier-B shots: `shots/2026-08-29-1040/`.

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

**NEXT ACTION:** **Commit the working tree** — the lap is complete and verified but deliberately
uncommitted (owner asked for the work to be split into commits by hand). Suggested split, in order:
1. `src/parkbench/byo.py` + `tests/test_byo.py` (the connector)
2. `src/parkbench/cli.py` `byo-run` + `tests/test_versioning.py` (the CLI surface)
3. `src/parkbench/profiles_server.py` + `tests/test_serve_profiles.py` (the `/byo` route)
4. `web/src/profiles.js` + `web/src/radar.js` + `autoloop/shots/2026-08-29-1040/` (Tier B)
5. docs: `02-decisions.md` (D-073) · `09` · `11` · `README.md` · `web/README.md` · backlog · this file
   · root `CLAUDE.md`

After that, the visual world has **no queued chunk** (chunk 4 is complete). The unblocking item is the
trust track's **`criterion-cohort`** (`docs/13` §B — needs a one-time online real-agent step). D-073
sharpened the case for the prerequisite: **BYO connectors for the solo rides** (roadmap #5) are now the
binding limit on measuring a third party at all (a BYO agent can only be scored on `social`, and so can
never appear on the career leaderboard), *and* they are what would supply the richer non-deterministic
roster the criterion cohort needs. Loose end still open: the economic/safety/social **discriminant
FAILs** (D-066/D-071) — per `docs/13` §E more rides cannot fix them; only a richer roster can.

**Blockers / needs-owner:** the uncommitted tree above is the only one. Optional: the D-065
`llm:<model-id>` agents run **live** only if `.env`'s `OPENROUTER_API_KEY` is valid — present as of
2026-07-22 (not validity-checked); the roster otherwise runs offline via the heuristic fallback. Note
`/byo` deliberately **refuses** the `llm` drivers regardless (a GET must not spend the API budget).
