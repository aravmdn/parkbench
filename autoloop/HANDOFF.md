# HANDOFF — the live baton

> The single source of truth for what's happening **right now**. Updated **write-ahead** (after every
> meaningful step, before any long op) — a usage cutoff can kill a session mid-step. **Git is ground
> truth for work done; this file is ground truth for intent / next action.** See
> [`../docs/10-autoloop.md`](../docs/10-autoloop.md) for the protocol.

---

**Updated:** 2026-09-01
**Loop state:** IDLE

**Active task:** — (none; `solo-ride-byo-connectors` complete and **committed**)
**Acceptance criteria:** met — see D-074 in `../docs/02-decisions.md`.
**Task branch:** none — worked directly on `main`. Built 2026-08-30, held uncommitted at the owner's
request, landed 2026-09-01 as the five commits listed in **NEXT ACTION** below.
**Tree state:** CLEAN · on `main`
**Last durable commit:** the D-074 docs commit (this file)

**This lap (2026-08-30): the solo BYO wire — D-074.** The park gains a **second** BYO wire so a third
party stops being a one-axis agent. `src/parkbench/solo_protocol.py` (message shapes) ·
`solo_server.py` (`SoloParkServer`: `GET /scenario` · `POST /plan` · `GET /health`) ·
`solo_client.py` (`drive_solo_agent`) carry the four **plan-shaped** solo rides — `economic` ·
`exchange` · `safety` · `containment` = both economic-axis rides and both safety-axis rides. Surfaced
as `parkbench byo-run --rides all|<subset>`, `parkbench serve --ride <name>`, `GET /byo?rides=all`,
and `byo.run_byo_profile(...)`. **A swept BYO profile covers `social` · `economic` · `safety`**, and
the `economic`/`safety` axes are *numerically identical* to a baseline's (both their rides are on the
wire); `social` stays partial because `commons` has no wire. All **16** wired legs (4 rides × 4
baselines) are byte-identical to in-process, `detail` included — the server runs the ride's own
`evaluate(..., agent=<bridge>)`, the lap's only engine change (an optional seam, inert when omitted).
`commons` and `coding` are **named with reasons** in `skipped_rides` + `source.unreachable`, guarded
by a test; a BYO agent still earns **no career**. **416 passing tests** (+47); purely additive — no
ride/scoring/fixture/`BENCHMARK_VERSION` change, and bare `byo-run` still emits the exact D-073
payload, so `web/` is untouched (Tier A only).

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

**NEXT ACTION:** — D-074 is **landed**. It went in as five commits on `main`:
1. `solo_protocol.py` + the `agent=` seam on the four solo `ride.py` files
2. `solo_server.py` + `solo_client.py`
3. `byo.py` (the sweep) + `cli.py` (`byo-run --rides`, `serve --ride`)
4. `profiles_server.py` (`/byo?rides=all`) + `tests/test_solo_wire.py`
5. docs: `02-decisions.md` (D-074) · `09` · `03` · `05` · `06` · `13` · `README.md` · backlog
   · this file · root `CLAUDE.md`

After that, the queue's top is the new **roadmap-#5 chunk** in [`backlog.md`](backlog.md):
`commons-byo-connector` → `coding-byo-connector` (together they unlock a BYO **career** — the roll-up
needs `integrity` from every ride), plus a Tier-B `byo-world-sweep` to show the three-axis capture in
the world and `byo-protocol-schema`. On the trust track the unblocking item is still the
**`criterion-cohort`** (`docs/13` §B — needs a one-time online real-agent step); D-074 partly unblocks
it (an external agent is now scorable on three axes) but its own binding constraint — a richer,
non-deterministic roster — is unchanged. Loose end still open: the economic/safety/social
**discriminant FAILs** (D-066/D-071) — per `docs/13` §E more rides cannot fix them; only a richer
roster can.

**Blockers / needs-owner:** the uncommitted tree above is the only one. Optional: the D-065
`llm:<model-id>` agents run **live** only if `.env`'s `OPENROUTER_API_KEY` is valid — present as of
2026-07-22 (not validity-checked); the roster otherwise runs offline via the heuristic fallback. Note
`/byo` deliberately **refuses** the `llm` drivers regardless (a GET must not spend the API budget).
