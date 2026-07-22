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
**Task branch:** `integration/parallel-laps-2026-07-22` (off `main` @ D-062) — an octopus-merge of the
three fan-out worktree branches `autoloop/task-byo-trainer` (49c0cc0) + `worktree-agent-af080d7b70967b48b`
(2bfe5bd) + `worktree-agent-a8002d1af62f49e6e` (b78a46e), plus a docs/decision-log consolidation commit.
**Not on `main`; not pushed.**
**Tree state:** clean · on `integration/parallel-laps-2026-07-22`
**Last durable commit:** the consolidation commit on that branch (see `git log -1`)

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

**NEXT ACTION:** **Owner decision** — land branch `integration/parallel-laps-2026-07-22` to `main`
(fast-forward or `--no-ff` merge, then optionally push to `origin`). It is fully verified (250 tests,
`export-profiles --check` 8 `ok`, `web/` build clean). After landing: move the three backlog/log records
to `log.md`, and decompose **chunk 4** from `docs/11-visual-world.md` "Next" (deferred live/served
`serve --profiles` endpoint; a BYO-over-the-wire *live* connector; richer per-land art). The trust
track's remaining *external* work is captured in `docs/13-external-validity-plan.md` (build "The Exchange"
economic ride first). Tier-B screenshot of the BYO trainer in the park is still to be captured (build is
green; the shot was deferred at integration).

**Blockers / needs-owner:**
1. Landing decision above (nothing false is on `main`; it still reads D-062 until landed).
2. Optional: to score the D-065 `llm:<model-id>` agents **live**, add one `OPENROUTER_API_KEY` to the
   gitignored `.env` (the owner creates the key; the roster works offline via heuristic fallback without it).
