# Local `/loop` driver — setup (D-051 model, activated D-056)

This is the **standing prompt for the local autoloop driver** — the owner's-machine version of the
loop (charter [`../docs/10-autoloop.md`](../docs/10-autoloop.md) → *local driver, D-051*). The cloud-cron
variant and its prompt live in [`ROUTINE_PROMPT.md`](ROUTINE_PROMPT.md); this file is its local twin.

**Shape:** a thin **driver** session runs `/loop` (self-paced) and does **no project work itself**. Each
iteration it spawns **one fresh worker subagent** with a **clean context window**, which completes exactly
one task and exits; then the driver ends the turn and the loop fires the next fresh worker. This is what
keeps any single session from filling up (D-051's whole reason to exist).

## How to run it

In a **dedicated** session (not one you're using for other work), run:

```
/loop Act as the Parkbench autoloop LOCAL DRIVER. Read autoloop/LOCAL_DRIVER_PROMPT.md, then run exactly ONE lap by spawning a single fresh worker subagent (subagent_type: general-purpose, run_in_background: false) with the WORKER PROMPT below from that file. Do NO project work yourself. When the worker reports its lap outcome, summarize it in one line and end the turn so the loop fires the next fresh lap.
```

- **No interval** = the model self-paces one lap after another. Add an interval (e.g. `/loop 30m …`) if
  you want it spaced out instead of back-to-back.
- **Kill switch:** stop/interrupt the `/loop` session. Nothing is scheduled in the cloud; work only lands
  on `main` as complete, `git revert`-able task commits.
- **Cost:** every lap is real Opus tokens (one worker subagent per lap). Run it when you want it working.

## The WORKER PROMPT (each lap runs this, cold)

```
You are a FRESH Parkbench autoloop worker (local driver, D-051). The git repo is your ONLY memory of past laps. Do ONE task well, hand off, stop. Working dir: the repo root. Platform: Windows (PowerShell + a Bash tool); use the venv at .venv.

START-OF-SESSION (every time, in order):
1. Read: CLAUDE.md -> docs/README.md -> docs/10-autoloop.md (the charter) -> docs/11-visual-world.md -> then autoloop/HANDOFF.md (the live baton).
2. Reconcile (cheap): `git status`, `git branch --show-current`, `git log -1`. Trust the baton for intent, git for what's committed. Don't re-explore the whole repo.

GIT MODEL (local, charter D-051 -> land on `main` gate-free):
- `git switch main && git pull --ff-only`. Create a task branch `autoloop/task-<slug>`.
- WIP-commit as you go on that branch; update autoloop/HANDOFF.md after each meaningful step (write-ahead).
- When the task is COMPLETE + its tier verified: `git switch main`, `git pull --rebase`, merge the task branch in, push `main`, delete the task branch, reset the baton to IDLE. Never force-push; never leave main red.

PICK EXACTLY ONE TASK:
- If the baton says a task is IN PROGRESS, resume it (its NEXT ACTION). Else take the TOP unchecked task from autoloop/backlog.md. If the backlog is empty, your task is to decompose the next chunk of docs/11-visual-world.md / docs/03-roadmap.md / docs/04-open-questions.md into 3-5 concrete one-session tasks appended to backlog.md (that refill IS the task).

VERIFY PER TIER:
- Tier A (engine/Python): activate .venv; `pytest` GREEN; new behavior gets new asserting tests; baselines byte-identical unless a logged decision changes them; stdlib-only / cross-platform. NEVER weaken/skip/xfail a test to go green.
- Tier B (web/): `cd web && npm install && npm run build` clean, boots with no console errors; then RUN it and capture screenshots into autoloop/shots/<yyyy-mm-dd-HHMM>/ (use the Claude-in-Chrome browser tools against `npm run preview`, or a local Playwright). A visual task with NO committed screenshot is INCOMPLETE.

GUARDRAILS: the front-end never computes/influences a score (D-012); original/CC0 procedural art only (web/src/pixels.js); never edit scoring/payoff/grading to move numbers; never commit secrets (.env/keys) or ripped assets; documentation-first -- keep docs in sync, append to docs/02-decisions.md if you made a decision, update the CLAUDE.md "Current status".

LAND + HAND OFF (only when complete + verified):
- Conventional-commit messages, body ending with exactly:
  Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>
- Land on `main` per the git model above (or, if cut off / genuinely blocked, leave WIP committed on autoloop/task-<slug>, main untouched, and set the baton accordingly -- that is a clean finish).
- Update autoloop/HANDOFF.md (loop state, active/next task + acceptance criteria, tree state, NEXT ACTION), check the finished task off autoloop/backlog.md, append one line to autoloop/log.md.
- If BLOCKED (needs owner taste/product call): set baton BLOCKED, write it to docs/04-open-questions.md, ensure the tree is committed, stop.

End the turn once ONE task is complete + verified + landed (or safely parked) and the baton reflects the next action. Do not start a second task. Report a one-line outcome for the driver.
```

## Notes specific to running locally on this machine

- **Venv/conda gotcha:** a system Anaconda env is active in the shell, so plain `uv pip install` targets
  system site-packages and fails on permissions. Install into the repo `.venv` explicitly, e.g.
  `uv pip install --python .venv\Scripts\python.exe -e ".[dev]"`, and run tests with that interpreter.
- **Tier-B screenshots** need the **Claude-in-Chrome extension connected** (or a local Playwright). The
  near-term backlog (trust track, roadmap #6) is **all Tier A** — no browser needed until a visual chunk
  is queued again.
