# Hourly autoloop — routine setup (D-054)

This is the **standing prompt** for the hourly cloud-cron build loop (decision D-054, charter
[`../docs/10-autoloop.md`](../docs/10-autoloop.md) → *cloud-cron mode*). Each firing spawns a **fresh
worker session** in the remote execution environment; the prompt is fully self-contained because the
worker starts cold with only the repo as memory.

## How to arm it

Create a scheduled routine that **creates a new session on each fire**, hourly, with the prompt below:

- **Via the app:** [claude.ai/code/routines](https://claude.ai/code/routines) → new routine → schedule
  **hourly** (cron `7 * * * *` — an off-:00 minute so the fleet doesn't stampede) → mode **fresh session
  per fire** → environment = this repo's environment → paste the prompt.
- **Via a session tool:** `create_trigger` with `create_new_session_on_fire: true`,
  `cron_expression: "7 * * * *"`, `notifications: {push: true}`, and `prompt` = the block below.

Kill switch: disable or delete the routine at [claude.ai/code/routines](https://claude.ai/code/routines)
(or `update_trigger enabled:false` / `delete_trigger`). Nothing auto-deploys — every lap lands only on a
branch + PR the owner still merges. Record the routine's `trig_…` id in `HANDOFF.md` once armed.

## The standing prompt

```
Autonomous hourly build loop for the Parkbench repo (aravmdn/parkbench). You are a FRESH worker session — the git repo is your ONLY memory of past laps. Do ONE task well, hand off, stop.

START-OF-SESSION (every time, in order):
1. Read: CLAUDE.md → docs/README.md → docs/10-autoloop.md (the charter) → docs/11-visual-world.md → then autoloop/HANDOFF.md (the live baton).
2. Reconcile (cheap): `git status`, `git branch --show-current`, `git log -1`. Trust the baton for intent, git for what's committed. Don't re-explore the whole repo.

GIT MODEL (cloud-cron, charter D-054): Work on branch `claude/next-tasks-j7f20o` and keep its PR updated — do NOT push to `main`. `git fetch origin && git checkout claude/next-tasks-j7f20o && git pull` first. If that branch's PR is already MERGED or CLOSED, start fresh: `git checkout -B claude/next-tasks-j7f20o origin/main`, and open a NEW draft PR after pushing. Never force-push a shared branch.

DO EXACTLY ONE TASK:
- Take the TOP unchecked task from autoloop/backlog.md and complete it. If the baton says a task is IN PROGRESS, resume that (its NEXT ACTION) instead. If the backlog is empty, your task is to decompose the next chunk of docs/11-visual-world.md / docs/03-roadmap.md into 3–5 concrete one-session tasks appended to backlog.md (that refill IS the task) — then stop, or take the new top task only if time is ample.
- WIP-commit as you go and update autoloop/HANDOFF.md after each meaningful step (write-ahead).

VERIFY PER TIER:
- Tier A (engine/Python): `pip install -e ".[dev]"` then `pytest` GREEN; baselines byte-identical unless a logged decision changes them; stdlib-only. Never weaken/skip/xfail a test to go green.
- Tier B (web/): `cd web && npm install && npm run build` clean; then RUN it and capture HEADLESS screenshots into autoloop/shots/<yyyy-mm-dd-HHMM>/ — launch Playwright Chromium at executablePath `/opt/pw-browsers/chromium` (import from /opt/node22/lib/node_modules/playwright/index.mjs), screenshot the vite preview, FAIL on console errors. A visual task with no committed screenshot is INCOMPLETE.

GUARDRAILS: the front-end never computes/influences a score (D-012); original/CC0 procedural art only (web/src/pixels.js); never edit scoring/payoff to move numbers; never commit secrets (.env/keys); documentation-first — keep docs in sync, append to docs/02-decisions.md if you made a decision, update the CLAUDE.md "Current status".

LAND + HAND OFF:
- Commit with a conventional-commit message whose body ENDS with exactly:
  Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>
- Push to `claude/next-tasks-j7f20o` (retry on network errors with backoff). Ensure an open draft PR exists; update its body if scope changed.
- HAND OFF so next hour's worker knows what to do: update autoloop/HANDOFF.md (loop state, active/next task + acceptance criteria, tree state, NEXT ACTION), check the finished task off autoloop/backlog.md, append one line to autoloop/log.md.
- If genuinely BLOCKED (needs owner taste/product call): set baton BLOCKED, write it to docs/04-open-questions.md, ensure the tree is committed + pushed, stop. That is a clean finish.

End the turn once ONE task is complete + verified + pushed and the baton reflects the next action. Do not start a second task.
```
