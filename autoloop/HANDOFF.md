# HANDOFF — the live baton

> The single source of truth for what's happening **right now**. Updated **write-ahead** (after every
> meaningful step, before any long op) — a usage cutoff can kill a session mid-step. **Git is ground
> truth for work done; this file is ground truth for intent / next action.** See
> [`../docs/10-autoloop.md`](../docs/10-autoloop.md) for the protocol.

---

**Updated:** 2026-09-02
**Loop state:** IDLE

**Active task:** — (none; `commons-byo-connector` complete and **committed**)
**Acceptance criteria:** met — see D-075 in `../docs/02-decisions.md`.
**Task branch:** none — worked directly on `main`, landed as seven commits.
**Tree state:** CLEAN · on `main`
**Last durable commit:** the D-075 docs commit (this file)

**This lap (2026-09-02): the commons BYO wire — D-075.** The park gains its **third and last-shaped**
BYO wire, and with it the `social` axis stops being the partial one.
`src/parkbench/commons_protocol.py` (message shapes) · `commons_server.py` (`CommonsParkServer`:
`GET /observation` · `POST /contribution` · `GET /health`) · `commons_client.py`
(`drive_commons_agent`) carry the `commons` ride as a **turn loop over a fully public game** — which
is neither shape the park already spoke: the negotiation wire is a turn loop over *hidden*
information, and the solo wire is public but *one-shot*. Surfaced as `parkbench serve --ride commons`
and folded into every sweep (`byo-run --rides all|commons`, `GET /byo?rides=all`,
`byo.run_byo_profile(...)`), which now drives **six legs**.

**The headline: every axis a BYO agent can reach is now numerically identical to a baseline's** — at
seed 1 for `heuristic`, social 0.9631180639047241 · economic 0.9804167854489221 · safety
0.7686518095569819, digit for digit. D-074 left one asymmetry (social was one ride where a baseline
got the mean of two) and recorded it honestly; this removes it. All four baselines are byte-identical
to in-process, `random` **included on purpose** — it is the only one that can catch a mistimed
re-seed, and `new_game` is sent once per game (round 0), never per round, so an agent's RNG carries
across a game's rounds. The wire's `history` carries the **whole society**, because the grim-trigger
reciprocator is only visible through it; nothing *helpful* (bracket, best response, running payoff,
cast hint) is sent, since an in-process baseline cannot see those either. **440 passing tests**
(+24); purely additive — no ride/scoring/fixture/`BENCHMARK_VERSION` change, and bare `byo-run` still
emits the exact D-073 payload (verified byte for byte), so `web/` is untouched (Tier A only).

**Two lists, one narrower.** `solo_protocol.UNREACHABLE_RIDES` stays the *plan wire's* own limit and
still lists `commons` — correctly, since that ride is unreachable by that wire and reachable by its
own. What a captured profile reports is the new `byo.NO_WIRE_RIDES`: rides with no wire at all, now
just `coding`.

**Prior lap (2026-08-30): the solo BYO wire — D-074.** The park gains a **second** BYO wire so a third
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

**NEXT ACTION:** — D-075 is **landed** (seven commits on `main`; D-074's five landed the day
before). The queue's top is now the **last** connector:

`coding-byo-connector` in [`backlog.md`](backlog.md) — submit-an-artifact, and it must reuse the
existing D-043/D-048 sandbox rather than add a second execution path. It is now the **only** thing
between a third party and a **career**, which is why the career-completeness rule (all rides vs. all
*reachable* rides) is worth settling **before** it lands rather than letting the answer fall out of
the implementation — raised in [`../docs/04-open-questions.md`](../docs/04-open-questions.md). Also
queued: a Tier-B `byo-world-sweep` to show the three-axis capture in the world (its wire note still
reads "wire scores negotiation only") and `byo-protocol-schema`. On the trust track the unblocking item is still the
**`criterion-cohort`** (`docs/13` §B — needs a one-time online real-agent step); D-074 partly unblocks
it (an external agent is now scorable on three axes) but its own binding constraint — a richer,
non-deterministic roster — is unchanged. Loose end still open: the economic/safety/social
**discriminant FAILs** (D-066/D-071) — per `docs/13` §E more rides cannot fix them; only a richer
roster can.

**Blockers / needs-owner:** the uncommitted tree above is the only one. Optional: the D-065
`llm:<model-id>` agents run **live** only if `.env`'s `OPENROUTER_API_KEY` is valid — present as of
2026-07-22 (not validity-checked); the roster otherwise runs offline via the heuristic fallback. Note
`/byo` deliberately **refuses** the `llm` drivers regardless (a GET must not spend the API budget).
