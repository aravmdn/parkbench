# HANDOFF — the live baton

> The single source of truth for what's happening **right now**. Updated **write-ahead** (after every
> meaningful step, before any long op) — a usage cutoff can kill a session mid-step. **Git is ground
> truth for work done; this file is ground truth for intent / next action.** See
> [`../docs/10-autoloop.md`](../docs/10-autoloop.md) for the protocol.

---

**Updated:** 2026-07-22
**Loop state:** IDLE

**Active task:** — (none; three parallel fan-out laps integrated + verified, awaiting land)
**Acceptance criteria:** —
**Task branch:** the three fan-out laps were octopus-merged onto `integration/parallel-laps-2026-07-22`
(worktree branches `autoloop/task-byo-trainer` 49c0cc0 + `worktree-agent-af080d7b70967b48b` 2bfe5bd +
`worktree-agent-a8002d1af62f49e6e` b78a46e, plus a consolidation commit), then **fast-forwarded into
`main` and pushed to `origin`.**
**Tree state:** clean · on `main`
**Last durable commit:** `git log -1` (the parallel-laps consolidation, now on `main`)

**Last integrated (2026-07-22):** **three parallel laps** run simultaneously as fresh worker sub-agents
in isolated worktrees (fully disjoint files), then merged + verified *together*:
- **D-063 `byo-trainer`** (Tier B, `web/`) — a BYO agent (`acme-bot`) renders as a "BYO"-chipped
  palette-swapped trainer; Tab/walk-up selects it → `S` stats screen shows its D-038 identity.
  `radar-byo.json` stand-in kept outside `export-profiles`' manifest. **Completes visual-world chunk 3.**
- **D-064 external-validity plan + criterion scaffold** (Tier A) — new Draft `docs/13-external-validity-plan.md`
  (recommends a second **economic** ride "The Exchange" next; criterion validity needs a one-time online
  step) + a not-yet-wired `criterion_validity()` scaffold in `validity.py`.
- **D-065 free-model roster** (Tier A) — curated free OpenRouter models registered as `llm:<model-id>`
  agents through the one key (`FREE_MODELS` in `agents/llm.py`); keyless heuristic fallback ⇒ tested offline.
Combined verification: **250 passing tests**, `export-profiles --check` 8 `ok` (exit 0), `web/` build
clean; seed-1 baselines byte-identical. Integration fixed the one real defect per-branch checks missed
(`test_export.py` manifest-coverage vs. the un-manifested BYO fixture). Prior lap: `live-profiles` (D-062,
now the "Prior status" block in `CLAUDE.md`). Per-lap: [`log.md`](log.md); narrative: root `CLAUDE.md`.

**Loop / active driver (D-056):** the owner-activated local `/loop` driver remains the standing
mechanism (`autoloop/LOCAL_DRIVER_PROMPT.md`). The **cloud-cron routine (D-054) stays DESIGNED +
UNARMED**.

**NEXT ACTION:** Loop is IDLE; the three parallel laps (D-063/064/065) are **landed on `main` + pushed**.
Next real work, either thread:
- **Visual world** — decompose **chunk 4** from `docs/11-visual-world.md` "Next" into `autoloop/backlog.md`
  (the deferred live/served `serve --profiles` endpoint so the world reads *fresh* data not fixtures; a
  BYO-over-the-wire *live* connector; richer per-land art). That refill is itself a task.
- **Trust track** — build the **economic 2nd ride "The Exchange"** (assignment/matching) per
  `docs/13-external-validity-plan.md`, unlocking the first economic monotrait pair in the MTMM matrix.
Loose end: the Tier-B screenshot of the BYO trainer is still uncaptured (build is green; live
canvas-capture was flaky against Kaplay's render loop) — recapture opportunistically.

**Blockers / needs-owner:** none. `main` reflects reality (landed + pushed). Optional: the D-065
`llm:<model-id>` agents run **live** only if `.env`'s `OPENROUTER_API_KEY` is valid — present as of
2026-07-22 (not validity-checked); the roster otherwise runs offline via the heuristic fallback.
