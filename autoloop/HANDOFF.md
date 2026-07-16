# HANDOFF — the live baton

> The single source of truth for what's happening **right now**. Updated **write-ahead** (after every
> meaningful step, before any long op) — a usage cutoff can kill a session mid-step. **Git is ground
> truth for work done; this file is ground truth for intent / next action.** See
> [`../docs/10-autoloop.md`](../docs/10-autoloop.md) for the protocol.

---

**Updated:** 2026-07-16
**Loop state:** IDLE

**Active task:** — (none)
**Acceptance criteria:** —
**Task branch:** `claude/project-progress-automation-pikvqv` (the Jul 9–16 daily-lap chain, PR #16 →
`main`; this chain ran as coordinator + fresh worker sub-agents rather than the D-056 local `/loop`)
**Tree state:** clean · on `claude/project-progress-automation-pikvqv`
**Last durable commit:** (see `git log -1`)

**Last landed (this chain, Jul 9–15):** seven daily laps — the **trust track drained** (D-058
input-ablation shortcut detector · D-059 structural bounded-horizon ladder · D-060 item hygiene
α + item-rest discrimination · D-061 bootstrap CIs + `benchmark_version` stamping; **223 passing
tests**, baselines byte-identical throughout) and **visual-world chunk 3 started** (chunk decomposed
into the backlog; `multi-trainers` + `fixture-provenance` landed with headless-verified screenshots).
Details per lap: [`log.md`](log.md); full narrative: root `CLAUDE.md` Current status.

**Loop / active driver (D-056):** the owner-activated local `/loop` driver remains the standing
mechanism (`autoloop/LOCAL_DRIVER_PROMPT.md`); this week's chain was a one-off coordinator session
doing the same lap protocol with dated daily commits onto a PR branch. The **cloud-cron routine
(D-054) stays DESIGNED + UNARMED**.

**NEXT ACTION:** Loop is IDLE. PR #16 (the Jul 9–16 chain) awaits owner review/merge. The backlog is
**not empty** — the next unchecked task is **`live-profiles`** (visual-world chunk 3, Tier A+B): a
live or freshly-exported data path for the spectator surfaces — either a read-only
`parkbench serve --profiles`-style endpoint (stdlib-only, tested) or a one-command static-export flow
regenerating all `web/` + `viewer/` fixtures; then **`byo-trainer`**. After chunk 3, the trust track's
remaining *external* work (criterion validity, a second ride per non-social axis, harder difficulty
tiers) is parked in `docs/12-validity.md` / `docs/04-open-questions.md`.

**Blockers / needs-owner:** review + merge PR #16 (or request changes); then pull `main` before the
next lap.
