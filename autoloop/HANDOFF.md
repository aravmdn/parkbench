# HANDOFF — the live baton

> The single source of truth for what's happening **right now**. Updated **write-ahead** (after every
> meaningful step, before any long op) — a usage cutoff can kill a session mid-step. **Git is ground
> truth for work done; this file is ground truth for intent / next action.** See
> [`../docs/10-autoloop.md`](../docs/10-autoloop.md) for the protocol.

---

**Updated:** 2026-07-08
**Loop state:** TASK IN PROGRESS

**Active task:** `convergent-validity` — MTMM/HTMT convergent+discriminant matrix over the four axes.
**Acceptance criteria:** `parkbench validity` emits the convergent correlation (social pair
negotiation×commons) + a discriminant matrix where the social same-axis correlation exceeds its
cross-axis (Campbell-Fiske row/column) correlations; new asserting tests; pytest green; baselines
byte-identical (purely additive measurement — no scoring/agent/ride edits).
**Task branch:** `autoloop/task-convergent-validity`
**Tree state:** clean · branch created off `main`
**Last durable commit:** (see `git log -1`)

**Findings (probe on eval seeds 4000-4007, roster random/greedy/heuristic — shared across ALL rides
incl. negotiation, which has no `optimal`):** social pair negotiation×commons ρ=+1.000; each
social-vs-(economic|safety) ρ=+0.500 ⇒ Campbell-Fiske discriminant PASSES. Structural limitation to
document: economic×safety (both single-ride axes) also ρ=+1.000 over this tiny roster — cannot yet be
shown distinct; the only true within-axis pair today is social.

**Loop / active driver (D-056):** the owner activated the **local `/loop` driver** (D-051 model) as the
active driver on 2026-07-08. Setup + the standing driver/worker prompt: `autoloop/LOCAL_DRIVER_PROMPT.md`.
Local laps work a `autoloop/task-<slug>` branch and **land on `main` gate-free**. The **hourly cloud-cron
routine (D-054) remains DESIGNED + DOCUMENTED but UNARMED** (its prompt is `autoloop/ROUTINE_PROMPT.md`;
arming is still blocked on owner approval of the scheduling MCP call) — use it only if switching back to
the cloud model. Note: the last recorded laps (through `world-signposts`, 2026-07-04) ran on the cloud
branch `claude/next-tasks-j7f20o`; the validity harness (D-055) + LLM-fallback landed as manual sessions,
not autoloop laps.

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

- **`world-signposts`** — overworld dressing: 4 crossroads lamps, a bench per land, a "PARKBENCH"
  entrance sign, and a bottom controls legend (`web/src/props.js` + lamp/bench sprites). Verified
  (Tier B, shot committed). **Chunk 2 is now complete.**

**PR state:** PR #13 (seed laps + chunk 2 through enter-gym-run) was **merged to `main`**. This branch
was restarted from the merged `main`; `world-signposts` is the first lap of a **new PR**.

**NEXT ACTION:** Loop is IDLE. The backlog is **not empty** — a later session queued the **trust track
(roadmap #6)** below the completed visual chunks. Pull the TOP unchecked backlog task, which is
**`convergent-validity`** (Tier A: an MTMM/HTMT convergent+discriminant matrix over the four axes — same-
axis correlation must exceed cross-axis; keep `pytest` green + baselines byte-identical). Create branch
`autoloop/task-convergent-validity` and begin. (A later refill can still decompose the next *visual*
chunk — live/served profiles, multiple trainers, a BYO-agent connector — once the trust track is drained.)

**Blockers / needs-owner:** none
