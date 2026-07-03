# HANDOFF — the live baton

> The single source of truth for what's happening **right now**. Updated **write-ahead** (after every
> meaningful step, before any long op) — a usage cutoff can kill a session mid-step. **Git is ground
> truth for work done; this file is ground truth for intent / next action.** See
> [`../docs/10-autoloop.md`](../docs/10-autoloop.md) for the protocol.

---

**Updated:** 2026-07-03
**Loop state:** TASK IN PROGRESS

**Active task:** `web-scaffold` — create the `web/` front-end app (Kaplay + Vite), blank canvas boots
with no console errors, short `web/README.md`.
**Acceptance criteria:** `web/` installs and builds clean, dev server serves a blank Kaplay canvas, a
screenshot committed to `autoloop/shots/<ts>/` (Tier B).
**Task branch:** `claude/next-tasks-j7f20o` (cloud session — designated branch; PR-gated, not push-to-main)
**Tree state:** dirty · scaffolding `web/`
**Last durable commit:** (see `git log -1`)

**Steps done this task:**
- Oriented: read charter + visual-world doc; confirmed node 22 / npm 10 / Playwright + Chromium available.

**NEXT ACTION:** Create `web/` (package.json with Vite + Kaplay, index.html, src booting a blank Kaplay
canvas, README), `npm install`, `npm run build`, screenshot the dev server headless, commit screenshot.

**Blockers / needs-owner:** none
