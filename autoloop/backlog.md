# Backlog — the task queue

Tasks pre-decomposed so each is completable in one session. Pull from the **top**. When this runs low,
a session decomposes the next chunk of [`../docs/11-visual-world.md`](../docs/11-visual-world.md) /
`../docs/03-roadmap.md` into 3–5 more tasks here (that refill is itself a valid task). Check a task off
and move its one-line record to [`log.md`](log.md) when it lands on `main`.

Format per task: `- [ ] <slug> — <goal>. **Done when:** <acceptance criteria> (Tier A/B).`

## Now (visual world — seed the front-end)

- [x] `web-scaffold` — Create the `web/` front-end app: Kaplay + a build/dev setup (e.g. Vite),
  `package.json`, a blank canvas that boots with no console errors, and a short `web/README.md`.
  **Done when:** `web/` installs and builds clean, the dev server serves a blank Kaplay canvas, and a
  screenshot of it is committed to `autoloop/shots/<ts>/` (Tier B). ✅ landed — see `autoloop/log.md`.
- [ ] `overworld-tilemap` — Render a small top-down tile overworld (GB/GBA palette) with **original**
  placeholder tiles (grass/path/water). **Done when:** the tilemap renders, builds clean, screenshot
  committed (Tier B).
- [ ] `four-lands` — Lay out the four **lands** (social / economic / coding / safety) as distinct
  regions/towns on the overworld, labeled. **Done when:** all four are visibly placed + labeled,
  screenshot committed (Tier B).
- [ ] `gym-buildings` — Place a **gym building** per ride in its land (negotiation, commons, economic,
  coding, safety), each enterable-looking. **Done when:** buildings render in the right lands,
  screenshot committed (Tier B).
- [ ] `trainer-sprite` — Add one **trainer sprite** with 4-direction walk-cycle animation, controllable
  or scripted to walk the overworld. **Done when:** the sprite animates and moves, screenshot/GIF
  committed (Tier B).
- [ ] `wire-radar-json` — Load a real `parkbench radar --json` fixture and render it as the **stats
  screen** (hex radar) reachable from the world. **Done when:** the stats screen shows real engine data
  for one agent, builds clean, screenshot committed (Tier B; may add a small fixture-gen helper — keep
  any engine-side code stdlib-only + tested, Tier A).

> Later chunks (deepen the world, Hall of Fame from `leaderboard --json`, badge/reputation visuals, a
> "trainer enters gym → run plays → result" flow) get decomposed here once the seed tasks land.
