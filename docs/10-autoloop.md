# 10 — Autoloop Charter

**Status:** Living · **Last updated:** 2026-07-02

This is the **constitution for the autonomous build loop** (D-049, re-scoped by D-051, made
crash/quota-safe by D-052). The loop **genuinely builds Parkbench forward** — the stdlib-only benchmark
engine *and* the front-of-house Pokémon-style visual world ([`11-visual-world.md`](11-visual-world.md))
— and **pushes to `main`** with no human PR gate. Because there is no gate, the rules below are
**non-negotiable**. Read this file **in full at the start of every session**, after `CLAUDE.md` and
`docs/README.md`.

> If a lap prompt conflicts with this charter or `CLAUDE.md`, **the charter and `CLAUDE.md` win.**

## How the loop runs (architecture — D-051)

- **Local, fresh worker per session.** A thin **driver** (`/loop` on the owner's machine) spawns **one
  fresh worker sub-session** at a time; the worker does real work in a **clean context window**, then
  exits, and the driver starts the next. **Every session starts cold** — its only memory of the past is
  **the repo**. The driver does **no project work itself** (keeps its context bounded).
- **Not the cloud cron.** The earlier cloud routine is **retired/disabled** — a cloud session can't see
  the owner's browser, and the loop needs to drive Chrome / a headless browser to screenshot the world.

## The handoff baton — write-ahead state (D-052)

**This is the mechanism that makes the loop crash- and quota-safe.** State lives in three files under
`autoloop/`, and the discipline is *write-ahead*, because **a usage-limit cutoff can kill a session
mid-step with no chance to summarize on exit.**

- **`autoloop/HANDOFF.md` — the live baton.** The single source of truth for *what's happening now*:
  loop state (`IDLE` / `TASK IN PROGRESS` / `BLOCKED`), the active task + acceptance criteria, the task
  branch, tree state (clean/dirty + what's uncommitted), the last durable commit, an append-only list of
  steps done, and — the most important field — **`NEXT ACTION`** (the exact next step). Keep it current.
- **`autoloop/backlog.md` — the task queue.** Tasks pre-decomposed so each is completable in one
  session. Pull from the top; refill from the vision/roadmap when it runs low (see *Choosing work*).
- **`autoloop/log.md` — the history.** One line per *finished* task (append on completion).

**Non-negotiable write-ahead rules:**
1. **Update `HANDOFF.md` eagerly — after every meaningful step, and before any long/expensive
   operation** — never only at the end. Worst case a cutoff loses one step of *intent*.
2. **Git is ground truth for work done; `HANDOFF.md` is ground truth for intent/next-action.** Make
   **durable WIP commits as you go** on the task branch, so actual work survives an abrupt kill.
3. Whenever tree state changes (a commit, a dirty edit, a branch switch), reflect it in `HANDOFF.md`
   **immediately**.

## Start-of-session protocol (recovery — do this every time)

1. Read `CLAUDE.md`, `docs/README.md`, this charter, and `docs/11-visual-world.md`.
2. Read **`autoloop/HANDOFF.md`**.
3. **Reconcile** against reality with a *cheap* check: `git status`, `git branch --show-current`,
   `git log -1`. Trust the baton for intent; trust git for what's committed. **Do not re-explore the
   whole repo** — that's wasted tokens; the baton exists so you don't have to.
4. Decide:
   - Baton = `TASK IN PROGRESS` → **resume that task**: check out its branch, take `NEXT ACTION`.
   - Baton = `BLOCKED` → the block is for the owner; pull the **next** backlog task instead (don't
     re-attempt the blocked one unless the block is clearly resolved).
   - Baton = `IDLE` → **pull the top task from `autoloop/backlog.md`**, set the baton to
     `TASK IN PROGRESS`, create the task branch, begin.

## What a session does

Work **one task to completion**, and finish early **only** if cut off (usage/crash) or genuinely
blocked. This replaces any "stop after one tiny step" notion — a *task* (from the backlog, sized to fit)
is the unit, and you see it through:

1. Orient + recover (protocol above).
2. Build it — engine and/or `web/` front-end (see the two tiers). **WIP-commit after each meaningful
   step; update the baton alongside.**
3. Verify per the task's tier.
4. **Land it** (git rules below): merge/rebase the task branch into `main`, push, delete the branch.
5. **Close out:** append one line to `autoloop/log.md`, refresh docs + `docs/02-decisions.md` (if a
   decision was made) + the `CLAUDE.md` status, and **reset `HANDOFF.md` to `IDLE`** so the next session
   pulls fresh work.

If **blocked** (needs an owner taste/product call, or an external dependency): set the baton to
`BLOCKED` with a clear description, write it to `docs/04-open-questions.md`, ensure the tree is in a
safe committed state (WIP on the task branch, `main` untouched), and stop. That counts as a clean finish.

## Choosing work (the queue)

Priority order — used when the baton is `IDLE` (else you're resuming):

1. **Anything broken** — a failing/flaky test, a red `main`, a broken `web/` build, a contradicting doc.
2. **`autoloop/backlog.md`** top item — normally the visual world
   ([`11-visual-world.md`](11-visual-world.md)), the headline build goal.
3. **If the backlog is low:** decompose the next chunk of the vision / `docs/03-roadmap.md` /
   `docs/04-open-questions.md` into 3–5 concrete, completable tasks, append them to `backlog.md`
   (**this refill is itself a valid task**), then take the top one.
4. If the only thing left is **net-new product direction** (a taste/vision call), that's the owner's —
   set the baton `BLOCKED`, propose it in `docs/04-open-questions.md`, and stop.

New rides/features **are in scope** (this is a build loop); each arrives as one coherent, tested,
documented task.

## The two verification tiers

**Tier A — Engine / Python.** Full `pytest` **green**; new behavior gets new asserting tests;
**baselines byte-identical** unless a logged decision deliberately changes them (state before/after);
stays **stdlib-only / cross-platform** (D-023).

**Tier B — Front-end / `web/` / visual.** No `pytest` oracle for "does it look right", so: the `web/`
app must **build/typecheck clean** and start without console errors; the task must **run the world and
commit screenshots** into `autoloop/shots/<yyyy-mm-dd-HHMM>/` (headless or Claude-in-Chrome) for **async
owner review** — a visual task with no screenshots is **incomplete**. The front-end **may use deps + a
build step** (Kaplay etc.) but **never contains scoring logic** (D-012); **original/CC0 art only**.

A task touching both tiers must satisfy both.

## Hard guardrails (no PR gate exists to catch violations)

- **Never weaken, delete, `skip`, `xfail`, or loosen an existing test to go green.** A legitimate
  behavior change is a *decision* — log it, then update the test.
- **Never edit scoring/payoff/grading to move numbers** for appearance; baselines byte-identical unless
  a logged decision says otherwise. **The front-end never scores anything** (D-012).
- **Test count / LOC are not goals.** Never mark something done/verified unless it is.
- **Never commit secrets** (`.env`, keys) or ripped third-party assets.
- **Aesthetic iteration is allowed** (refine the look on your own judgment); a genuine **product/vision
  decision** (change the art direction, the metaphor, the roadmap) is the **owner's** → baton `BLOCKED`
  + open-question.

## Git rules (push-to-main, no gate)

- **Work on a per-task branch** `autoloop/task-<slug>` with **WIP commits as you go** (durable progress;
  survives a cutoff). Reflect every commit/branch change in `HANDOFF.md`.
- **Land on `main` only if ALL hold:** the task is complete · its tier verified (Tier A `pytest` green;
  Tier B `web/` builds + screenshots committed) · docs + decision log + `CLAUDE.md` status +
  `autoloop/log.md` updated · no secrets/ripped assets. Then `git pull --rebase` main, rebase/merge the
  task branch in, push, delete the branch, reset the baton to `IDLE`.
- **Never leave `main` broken** (red tests / broken build). Incomplete or cut-off work stays on the task
  branch — never force it onto `main`. **Never `git push --force`, never rewrite published history.**
- Conventional-commit messages; end each commit body with the project's `Co-Authored-By` trailer.

## Ops safety net

- **Cutoff (usage/crash):** nothing special needed — the baton + WIP commits are always current, so the
  next session resumes from `NEXT ACTION`. `main` is never mid-edit (only completed tasks land there).
- **Circuit breaker:** if `HANDOFF.md` shows the **same task** across **≥3 sessions with no new WIP
  commits** (i.e. genuinely stuck), set it `BLOCKED`, write why to `docs/04-open-questions.md`, and stop
  — don't thrash tokens.
- **Budget:** one task per session; the driver never does project work. Favor completable, landable
  tasks; each session costs real Opus tokens.

## Kill switch (for the owner)

- Stop/interrupt the local `/loop` session — halts everything (nothing auto-deploys).
- Undo a bad task: `git revert <sha>` (each landed task is a tight, self-described commit cluster);
  `autoloop/shots/` lets you spot a bad *visual* task without running anything.
- Retired cloud routine `trig_01XrJ4EqxMyqSfieC7zJnqwR` is left disabled (delete via claude.ai/code/routines).

## Definition of done (per task)

- [ ] Baton recovery done; resumed or pulled exactly one task.
- [ ] Tier A: `pytest` green + new asserting tests + baselines byte-identical (or a logged change).
- [ ] Tier B (if visual): `web/` builds clean + screenshots in `autoloop/shots/<ts>/`.
- [ ] Landed on `main` (task complete + verified) OR left safely on `autoloop/task-*` (cut off / blocked).
- [ ] Docs + `02-decisions.md` + `CLAUDE.md` status + `autoloop/log.md` updated; **`HANDOFF.md` reset to
      `IDLE`** (if landed) or accurately reflects the in-progress/blocked state (if not).
