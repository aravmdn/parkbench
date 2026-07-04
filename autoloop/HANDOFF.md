# HANDOFF — the live baton

> The single source of truth for what's happening **right now**. Updated **write-ahead** (after every
> meaningful step, before any long op) — a usage cutoff can kill a session mid-step. **Git is ground
> truth for work done; this file is ground truth for intent / next action.** See
> [`../docs/10-autoloop.md`](../docs/10-autoloop.md) for the protocol.

---

**Updated:** 2026-07-03
**Loop state:** IDLE

**Active task:** — (none)
**Acceptance criteria:** —
**Task branch:** `claude/next-tasks-j7f20o` (cloud-cron model, D-054 — push here + keep PR #13 updated,
never to `main`)
**Tree state:** clean · on `claude/next-tasks-j7f20o`
**Last durable commit:** (see `git log -1`)

**Loop:** the **hourly cloud-cron autoloop is DESIGNED + DOCUMENTED (D-054) but NOT YET ARMED.** The
standing worker prompt is committed at `autoloop/ROUTINE_PROMPT.md`; arming the durable hourly trigger
(`create_trigger`, fresh-session-per-fire, cron `7 * * * *`) is **blocked on an owner approval of the
scheduling MCP call** and must be done from the app (claude.ai/code/routines) or a session where that
approval clears. Record the routine's `trig_…` id here once armed. Until then, the loop advances only
when a session is run manually against this baton.

**Steps done (chunk-2 iterations landed on the branch):**
- Refilled the backlog with **visual-world chunk 2** (`hall-of-fame`, `badge-reputation`,
  `enter-gym-run`, `world-signposts`).
- **`hall-of-fame`** — leaderboard scene reachable with `H` (Tier B, shots committed).
- **`badge-reputation`** — the stats screen (`S`) now shows a **gym-badge row + reputation** from the
  verbatim `leaderboard --json` legs: earned (bright + check) / cracked (dim + red X) / skipped (faint
  dash); reputation colour-coded. Verified on heuristic/greedy/optimal (Tier B, shots committed).
- **`enter-gym-run`** — the trainer now carries an **agent identity** (name tag) and walking it onto a
  gym triggers an overlay beat: **"NOW RIDING" → SCORE** (that agent+ride's real `radar --json` score),
  then returns to the world. `web/src/gymrun.js` + trainer `paused` state. Verified (Tier B, shots).
- Documented the hourly loop: decision **D-054**, charter cloud-cron mode, `CLAUDE.md` status,
  `autoloop/ROUTINE_PROMPT.md`.

**NEXT ACTION:** Loop is IDLE. Top unchecked backlog task is **`world-signposts`** (park entrance sign,
per-land flavor props from new procedural tiles, and a small legend for the four lands + `S`/`H`
controls). Pull it per the start-of-session protocol. That's the **last** chunk-2 task; after it, refill
the backlog with the next chunk (live/served profiles, multiple trainers, a BYO connector).

**Blockers / needs-owner:** none
