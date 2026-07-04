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

**Steps done this (iteration 1) task:**
- Refilled the backlog with **visual-world chunk 2** (`hall-of-fame`, `badge-reputation`,
  `enter-gym-run`, `world-signposts`).
- Built + landed **`hall-of-fame`** (Tier B: build clean, headless screenshot, zero console errors,
  `autoloop/shots/…/hall-of-fame.png`) — a leaderboard scene reachable with `H`.
- Documented the hourly loop: decision **D-054**, charter `docs/10-autoloop.md` (cloud-cron mode + git
  model + kill switch), `CLAUDE.md` status.

**NEXT ACTION:** Loop is IDLE. Top unchecked backlog task is **`badge-reputation`** (show each agent's
career/reputation as earned vs. revoked gym badges on the stats screen, from `career --json` /
leaderboard `legs`). Pull it per the start-of-session protocol.

**Blockers / needs-owner:** none
