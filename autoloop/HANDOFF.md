# HANDOFF — the live baton

> The single source of truth for what's happening **right now**. Updated **write-ahead** (after every
> meaningful step, before any long op) — a usage cutoff can kill a session mid-step. **Git is ground
> truth for work done; this file is ground truth for intent / next action.** See
> [`../docs/10-autoloop.md`](../docs/10-autoloop.md) for the protocol.

---

**Updated:** 2026-07-22
**Loop state:** IDLE

**Active task:** — (none)
**Acceptance criteria:** —
**Task branch:** `autoloop/task-live-profiles` → `main` (this lap ran in a normal owner session after a
`git pull`/merge; PR #16's daily-lap chain was already merged upstream into `main`)
**Tree state:** clean · on `main`
**Last durable commit:** (see `git log -1`)

**Last landed (2026-07-22):** **`live-profiles`** (visual-world chunk 3, D-062) — `parkbench
export-profiles` [`--check`] (new `src/parkbench/export.py`) regenerates all 8 `web/`+`viewer/`
spectator fixtures verbatim from the versioned CLI in one command (chose the static-export option (b);
the live HTTP endpoint option (a) is deferred to `docs/04-open-questions.md`). `--check` exits 1 on
drift (standing provenance guard, `tests/test_export.py`, **239 passing tests**, +16). Ranking logic
consolidated into `career.build_leaderboard()`. Comparison is float-repr-tolerant (12 dp) + LF-canonical
⇒ portable across Windows/Linux. Baselines byte-identical; Tier-B shots in
`autoloop/shots/2026-07-22-1456/`. Before this: the Jul 9–16 chain (PR #16, now on `main`) drained the
trust track (D-058→D-061) and started chunk 3 (`multi-trainers`, `fixture-provenance`). Per-lap:
[`log.md`](log.md); narrative: root `CLAUDE.md`.

**Loop / active driver (D-056):** the owner-activated local `/loop` driver remains the standing
mechanism (`autoloop/LOCAL_DRIVER_PROMPT.md`). The **cloud-cron routine (D-054) stays DESIGNED +
UNARMED**.

**NEXT ACTION:** Loop is IDLE. The next unchecked backlog task is **`byo-trainer`** (visual-world
chunk 3, Tier B, no engine code): render a BYO agent (per `docs/09-byo-protocol.md`) as an additional
palette-swapped, distinctly-labeled trainer alongside the baselines, from a completed run's identity
JSON (D-038). When chunk 3 closes, decompose chunk 4 from `docs/11-visual-world.md` "Next". The trust
track's remaining *external* work (criterion validity, a second ride per non-social axis, harder
difficulty tiers) + the deferred live `serve --profiles` endpoint are parked in `docs/12-validity.md`
/ `docs/04-open-questions.md`.

**Blockers / needs-owner:** none. `main` reflects reality (this lap committed + pushed).
