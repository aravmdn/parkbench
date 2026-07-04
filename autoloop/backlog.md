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
- [x] `overworld-tilemap` — Render a small top-down tile overworld (GB/GBA palette) with **original**
  placeholder tiles (grass/path/water). **Done when:** the tilemap renders, builds clean, screenshot
  committed (Tier B). ✅ landed — procedural grass/path/water/tree tiles, crossroads + pond.
- [x] `four-lands` — Lay out the four **lands** (social / economic / coding / safety) as distinct
  regions/towns on the overworld, labeled. **Done when:** all four are visibly placed + labeled,
  screenshot committed (Tier B). ✅ landed — accent-tinted quadrants + town signs (name + axis).
- [x] `gym-buildings` — Place a **gym building** per ride in its land (negotiation, commons, economic,
  coding, safety), each enterable-looking. **Done when:** buildings render in the right lands,
  screenshot committed (Tier B). ✅ landed — accent-roofed gym sprite per ride, nameplated.
- [x] `trainer-sprite` — Add one **trainer sprite** with 4-direction walk-cycle animation, controllable
  or scripted to walk the overworld. **Done when:** the sprite animates and moves, screenshot/GIF
  committed (Tier B). ✅ landed — procedural 3×4 walk-cycle sheet, arrow-key control + auto-patrol.
- [x] `wire-radar-json` — Load a real `parkbench radar --json` fixture and render it as the **stats
  screen** (hex radar) reachable from the world. **Done when:** the stats screen shows real engine data
  for one agent, builds clean, screenshot committed (Tier B; may add a small fixture-gen helper — keep
  any engine-side code stdlib-only + tested, Tier A). ✅ landed — 4-axis radar from verbatim
  `radar --json` fixtures (heuristic/greedy/optimal/random), reachable with `S`, cycle with ← →.

> **All six visual-world seed tasks are done.**

## Now (visual world — chunk 2: spectator payoffs)

Decomposed 2026-07-03 from `docs/11-visual-world.md` "Next" + `docs/03-roadmap.md` #4. Same rules: pull
from the top; each is one-session-sized; Tier B unless it adds engine code (then Tier A too).

- [x] `hall-of-fame` — A **Hall of Fame** scene rendering the ranked leaderboard from a verbatim
  `parkbench leaderboard --json` fixture (career score + capability × reputation bars per agent),
  reachable from the world (e.g. press `H`). **Done when:** the scene shows the real ranking for ≥4
  agents, builds clean, no console errors, screenshot committed (Tier B; fixture is verbatim CLI JSON —
  no engine code). ✅ landed — ranked career bars (optimal>heuristic>random>greedy), reachable with `H`.
- [x] `badge-reputation` — On the **stats screen**, show each agent's **career/reputation** as earned
  vs. revoked **gym badges** (a badge per ride; dimmed/cracked when that ride's `integrity` is 0 or the
  agent's reputation collapsed), from the `career --json` (or leaderboard `legs`) fixture. **Done when:**
  badges reflect real per-ride integrity for ≥2 contrasting agents (e.g. `optimal` vs `greedy`),
  screenshot committed (Tier B). ✅ landed — badge row + reputation on the stats screen (greedy's SAF
  cracked, optimal all-earned w/ skipped NEG).
- [x] `enter-gym-run` — First cut of the **"trainer enters gym → result"** flow: walking the trainer
  onto a gym tile triggers a short "now riding…" beat, then reveals that agent+ride's **score** from a
  fixture (per-ride score already in the radar/leaderboard JSON). **Done when:** stepping into ≥1 gym
  shows its real score and returns to the world, builds clean, screenshot committed (Tier B). ✅ landed —
  overlay state machine; trainer (heuristic) into the economic gym → "NOW RIDING" → SCORE 0.990.
- [ ] `world-signposts` — Deepen the overworld: a **park entrance sign**, per-land flavor props
  (benches/lamps/fences from new procedural tiles), and a small legend so the four lands + the `S`/`H`
  controls are discoverable. **Done when:** the additions render, build clean, screenshot committed
  (Tier B).

> Later chunks (live/served profiles instead of fixtures; multiple trainers on-screen; a BYO-agent
> connector to the world) get decomposed here once chunk 2 lands.
