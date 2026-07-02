# 10 — Autoloop Charter

**Status:** Living · **Last updated:** 2026-07-02

This is the **constitution for the autonomous self-development loop** (D-049). A scheduled agent runs
one **lap** of this loop roughly **every 5 hours**, unattended, and **pushes to `main`** with no human
PR gate. Because there is no gate, the rules below are **non-negotiable**: the test suite, the
byte-identical baselines, and the "stop when unclear" rule are the *only* safety net. Read this file
**in full at the start of every lap**, after `CLAUDE.md` and `docs/README.md`.

> If any instruction here conflicts with a lap prompt, **this charter and `CLAUDE.md` win.** A lap
> prompt may narrow the scope but may never relax a guardrail below.

## What a lap is (the only shape of work allowed)

One lap = **one smallest-viable, coherent unit of work**, start to finish:

1. **Orient.** Read `CLAUDE.md`, `docs/README.md`, this file, and the doc(s) relevant to the item.
   The doc set grows — re-read, never assume.
2. **Pick exactly one item** from the queue (see *Choosing work* below). If nothing is clearly
   actionable, **do not invent work** — write a proposal into `docs/04-open-questions.md`, commit that,
   and stop the lap.
3. **Plan briefly**, then **implement** on `main` (working tree; see *Git rules*).
4. **Verify.** Run the **full** suite (`pytest`). It must be **green**. Add tests that genuinely
   exercise the new behavior.
5. **Document in the same lap.** Update the relevant doc(s), append a decision entry to
   `docs/02-decisions.md`, and refresh the **Current status** block in `CLAUDE.md` (where things
   stand · what's next · how to verify).
6. **Land it.** Only if the push preconditions (below) are met, commit and push to `main`. Then stop.

**One item per lap. No exceptions.** If the item turns out bigger than a lap, split off the smallest
shippable slice, ship that, and park the rest in `docs/04-open-questions.md` or `docs/03-roadmap.md`.

## Choosing work (the queue)

Pick the next actionable item, in this priority order:

1. **Anything broken** — a failing/flaky test, red `main`, a doc that contradicts the code. Fix first.
2. **`docs/04-open-questions.md`** — the highest-value *open* item that is concretely actionable now.
3. **`docs/03-roadmap.md`** — in roughly listed order. The live frontiers are **#5 (BYO ecosystem /
   full OS sandbox)** and **#4 (spectator product)**.
4. The **Next** bullets in the `CLAUDE.md` status block.

Prefer the item with the clearest **objective acceptance signal** (a test can decide it) over anything
that needs a product/taste judgment. Punt taste calls to open-questions for the human.

## Hard guardrails (never violate — these have no PR gate to catch them)

- **Never weaken, delete, `skip`, `xfail`, or loosen an existing test to make the suite pass.** If a
  change legitimately alters expected behavior, that is a *decision* — log it in `02-decisions.md` with
  the rationale, and only then update the test.
- **Never edit scoring formulas, payoff math, or ride grading to change results** for appearance's
  sake. **Baselines stay byte-identical** unless a logged decision explicitly and deliberately changes
  them (state the before/after numbers in the decision, per the D-043/D-048 precedent).
- **Test count is not a goal.** New tests must assert new behavior, not pad the number.
- **Never mark something done, verified, or passing unless it actually is.** Report failures honestly
  in the status block and stop.
- **Respect v1 scope discipline** (`CLAUDE.md` rule 4): no silent scope creep. Out-of-scope ideas go to
  the roadmap/open-questions, not the build.
- **Never commit secrets** (`.env`, API keys, `OPENROUTER_API_KEY`, tokens). They are gitignored — keep
  it that way.
- **Stay stdlib-first / cross-platform (Windows-first)** per D-023. No new runtime dependency without a
  logged decision.
- **When blocked, ambiguous, out of budget, or facing a judgment call → STOP.** Write what you found to
  `docs/04-open-questions.md` and end the lap cleanly. Guessing is forbidden.

## Git rules (push-to-main, no gate — D-049)

- **Push to `main` only if ALL hold:** full `pytest` is green · the work is one coherent, complete item
  · docs + decision log + `CLAUDE.md` status are updated in the same lap · no secrets staged.
- **If the suite is red or the item is unfinished at end of budget: do NOT push to `main`.** Instead
  commit the WIP to a branch named `autoloop/wip-<yyyy-mm-dd-HHMM>`, note the state in
  `docs/04-open-questions.md`, and stop. **`main` must never be left red.**
- **Before pushing:** integrate the remote (`git pull --rebase`); if it won't rebase cleanly, stop and
  park a note. **Never `git push --force`, never rewrite published history, never touch other branches'
  history.**
- Conventional-commit messages (the repo's existing style), and end each commit body with the
  `Co-Authored-By` trailer this project uses.
- **Leave every lap resumable** (`CLAUDE.md` rule 5): a fresh session must be able to continue from
  `CLAUDE.md` + `docs/` alone.

## Budget & cost

- **One item per lap; do not chain laps.** The schedule fires the next lap; don't pre-empt it.
- Prefer doing the work **inline**. Spawning sub-agents is the expensive path — only do it when a lap
  genuinely needs parallel isolated work, and never recursively.
- If a lap has produced nothing shippable within a reasonable working budget, **stop and park a note**
  rather than thrashing.

## Kill switch (for the human)

- **Pause/stop the schedule:** `/schedule` (list/manage routines) and disable or delete the Parkbench
  autoloop routine — see the setup notes in that routine's description.
- **Emergency stop mid-lap:** interrupt the session, or delete the routine; nothing here auto-merges or
  deploys, so stopping the schedule fully halts it.
- **If a bad lap lands on `main`:** every lap is one commit (or a tight cluster) with a decision-log
  entry, so `git revert <sha>` cleanly undoes it. That is why one-item-per-lap is load-bearing.

## Definition of done (per lap)

- [ ] Exactly one queue item addressed (or a proposal parked, if nothing was actionable).
- [ ] `pytest` fully green; new behavior has new asserting tests; baselines byte-identical (or a logged
      decision explains the change).
- [ ] Relevant doc(s) updated, decision appended to `02-decisions.md`, `CLAUDE.md` status refreshed.
- [ ] Committed and pushed to `main` **iff** the push preconditions held; otherwise parked on a
      `autoloop/wip-*` branch with a note.
