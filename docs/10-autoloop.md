# 10 — Autoloop Charter

**Status:** Living · **Last updated:** 2026-07-02

This is the **constitution for the autonomous build loop** (D-049, re-scoped by D-051). The loop's job
is to **genuinely build Parkbench forward** — both the behind-the-scenes benchmark engine *and* the
front-of-house Pokémon-style visual world ([`11-visual-world.md`](11-visual-world.md)) — one **lap** at
a time, and **push to `main`** with no human PR gate. Because there is no gate, the rules below are
**non-negotiable**. Read this file **in full at the start of every lap**, after `CLAUDE.md` and
`docs/README.md`.

> If a lap prompt conflicts with this charter or `CLAUDE.md`, **the charter and `CLAUDE.md` win.**

## How the loop runs (architecture — D-051)

- **Local, fresh worker per lap.** A thin **driver** runs on the owner's machine (a `/loop` session).
  Each iteration the driver spawns **one fresh sub-session (worker)** that performs the entire lap in a
  **clean context window**, then returns a short summary; the driver records nothing but that summary
  and starts the next lap. **This means every lap starts cold** — the worker's only memory of past laps
  is **the repo** (`CLAUDE.md`, `docs/`, the decision log, `autoloop/log.md`, committed screenshots).
  Re-derive state from the repo every lap; never assume continuity from a previous lap.
- **The driver does no project work itself** — it only dispatches — so its context stays small.
- **Not the cloud cron.** The earlier cloud routine (D-049 as first drafted) is **retired/disabled**; a
  cloud session can't see the owner's browser. The loop is local so it can drive Chrome and screenshot
  the world.

## What a lap is

One lap = **one smallest-viable, coherent unit of forward progress**, start to finish:

1. **Orient.** Read `CLAUDE.md`, `docs/README.md`, this charter, `docs/11-visual-world.md`, and the
   doc(s) relevant to the item.
2. **Pick exactly one item** (see *Choosing work*). If nothing is clearly actionable, propose it in
   `docs/04-open-questions.md`, commit that, and stop.
3. **Build it** (engine work and/or `web/` front-end work — see the two tiers below).
4. **Verify** per the item's tier.
5. **Document in the same lap:** update the relevant doc(s), append a decision to
   `docs/02-decisions.md`, refresh the **Current status** block in `CLAUDE.md`, and append one line to
   `autoloop/log.md` (date · item · verify status · commit sha or wip-branch).
6. **Land it** per the push rules, then stop.

**One item per lap.** If it's bigger than a lap, ship the smallest slice and park the rest.

## Choosing work (the queue)

Priority order:

1. **Anything broken** — a failing/flaky test, a red `main`, a broken `web/` build, a doc that
   contradicts the code. Fix first.
2. **The visual world** ([`11-visual-world.md`](11-visual-world.md)) — this is the headline build goal.
   Early laps: scaffold `web/` (Kaplay + build), render the overworld + the four lands + gym buildings,
   a walking trainer sprite, then wire real engine JSON into the stats screen / Hall of Fame. Then
   deepen it lap by lap.
3. **`docs/04-open-questions.md`** — the highest-value concretely-actionable open item.
4. **`docs/03-roadmap.md`** in order, then the `CLAUDE.md` **Next** bullets.

Prefer items with a clear acceptance signal. New rides/features **are in scope** (this is a build loop),
but each must arrive as one coherent, tested, documented lap.

## The two verification tiers

**Tier A — Engine / Python / behind-the-scenes.** The bar is unchanged and strict:
- Full `pytest` must be **green**; new behavior gets new asserting tests; **baselines byte-identical**
  unless a logged decision deliberately changes them (state before/after numbers).
- Stays **stdlib-only / cross-platform** (D-023). No new *engine* runtime dependency without a decision.

**Tier B — Front-end / `web/` / visual.** There is no `pytest` oracle for "does it look right", so:
- The `web/` app must **build/typecheck cleanly** and start without console errors.
- The lap must **run the world and commit screenshots** into `autoloop/shots/<yyyy-mm-dd-HHMM>/`
  (headless browser, or Claude-in-Chrome against the local dev server) so the owner reviews the look
  **async** and can revert. A visual lap with no screenshots is **incomplete** — do not push it to
  `main`; park it.
- The front-end **may use dependencies and a build step** (Kaplay etc.) — this is the sanctioned
  exception to the engine's stdlib-only rule. It must **never contain scoring logic** (D-012); it only
  renders engine JSON.
- **Original art only** — never ripped third-party (Nintendo/Pokémon) assets (see
  [`11-visual-world.md`](11-visual-world.md)).

A lap that touches both tiers must satisfy both.

## Hard guardrails (no PR gate exists to catch violations)

- **Never weaken, delete, `skip`, `xfail`, or loosen an existing test to go green.** A legitimate
  behavior change is a *decision* — log it, then update the test.
- **Never edit scoring/payoff/grading to move numbers** for appearance. Baselines byte-identical unless
  a logged decision says otherwise.
- **The front-end never scores anything** — presentation only (D-012).
- **Test count / lines of code are not goals.** New tests must assert new behavior.
- **Never mark something done/verified/passing unless it is.** Report failures honestly and stop.
- **Never commit secrets** (`.env`, API keys) or ripped third-party assets.
- **When blocked, ambiguous, out of budget, or facing a taste/product call the owner should make →
  STOP.** Write it to `docs/04-open-questions.md` and end the lap. Guessing is forbidden. (Aesthetic
  *iteration* is allowed — the loop refines the look on its own judgment — but a genuine product
  decision, e.g. changing the whole art direction or metaphor, is the owner's.)

## Git rules (push-to-main, no gate)

- **Push to `main` only if ALL hold:** the item is complete · its tier's verification passed (Tier A:
  `pytest` green; Tier B: `web/` builds + screenshots committed) · docs + decision log + `CLAUDE.md`
  status + `autoloop/log.md` updated · no secrets or ripped assets staged.
- **Otherwise do NOT push to `main`.** Commit WIP to `autoloop/wip-<yyyy-mm-dd-HHMM>`, note the state in
  `docs/04-open-questions.md`, and stop. **`main` is never left broken (red tests or a broken build).**
- Before pushing: `git pull --rebase`; if it won't rebase cleanly, stop and park a note. **Never
  `git push --force`, never rewrite published history.**
- Conventional-commit messages; end each commit body with the project's `Co-Authored-By` trailer.
- **Leave every lap resumable** (`CLAUDE.md` rules 3 & 5).

## Budget & cost

- **One item per lap.** The worker does one lap and exits; the driver starts the next. Don't chain.
- The worker does the heavy work in its own fresh context; the **driver must not** do project work
  (keeps its context bounded). The worker should also avoid spawning further sub-agents unless a lap
  genuinely needs parallel isolated work — never recursively.
- If a lap produces nothing shippable within a reasonable budget, **stop and park a note** rather than
  thrashing. Each lap costs real tokens (Opus) — favor small, complete, landable slices.

## Kill switch (for the owner)

- **Stop the loop:** interrupt / end the local `/loop` session. That halts everything — nothing
  auto-deploys.
- **Retired cloud routine:** `trig_01XrJ4EqxMyqSfieC7zJnqwR` is left **disabled**; delete it via
  https://claude.ai/code/routines if desired.
- **Undo a bad lap:** every lap is one commit (or a tight cluster) with a decision-log entry and an
  `autoloop/log.md` line, so `git revert <sha>` cleanly undoes it. Screenshots in `autoloop/shots/` let
  you spot a bad *visual* lap without running anything.

## Definition of done (per lap)

- [ ] Exactly one queue item addressed (or a proposal parked, if nothing was actionable).
- [ ] Tier A: `pytest` green + new asserting tests + baselines byte-identical (or a logged change).
- [ ] Tier B (if visual): `web/` builds clean + screenshots committed to `autoloop/shots/<ts>/`.
- [ ] Docs updated · decision appended to `02-decisions.md` · `CLAUDE.md` status refreshed ·
      `autoloop/log.md` line added.
- [ ] Pushed to `main` **iff** the push preconditions held; else parked on `autoloop/wip-*` with a note.
