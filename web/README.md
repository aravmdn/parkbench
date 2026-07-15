# `web/` — the Parkbench visual world

The **front-of-house** for Parkbench: a Pokémon-style, Game Boy / GBA-era pixel world where each agent
is a **trainer** who walks the park and steps into **gyms** (the rides) to be benchmarked. See
[`../docs/11-visual-world.md`](../docs/11-visual-world.md) for the full vision and
[`../docs/10-autoloop.md`](../docs/10-autoloop.md) for how it gets built.

> **Load-bearing rule (D-012):** this app is **presentation only**. It never computes or influences a
> score — it *reads* the stdlib engine's JSON (`parkbench radar --json`, `career --json`,
> `leaderboard --json`, run logs) and draws it. All truth stays in the engine.
>
> The committed fixtures under `src/fixtures/` are verbatim CLI output and carry the engine's
> `benchmark_version` stamp (D-061); the stats screen and Hall of Fame surface it (`bench v1.0.0`) so a
> spectator always knows which benchmark version produced the numbers on screen. To refresh, re-run the
> same `parkbench ... --json` commands and overwrite the files.

## Stack

- **[Kaplay](https://kaplayjs.com/)** — the maintained Kaboom.js fork; pixel sprites, animation frames,
  tilemap levels, scenes.
- **[Vite](https://vitejs.dev/)** — dev server + build. Unlike the engine (stdlib-only, D-023), the
  front-end is allowed dependencies and a build step.

## Run it

```sh
cd web
npm install
npm run dev      # dev server with hot reload → http://localhost:5173
npm run build    # production build → web/dist/
npm run preview  # serve the production build locally
```

A blank/placeholder Kaplay canvas should boot with **no console errors**.

## In the world

- **The full baseline roster walks the park at once** — one trainer per agent
  (`heuristic` / `greedy` / `optimal` / `random`), each palette-swapped (procedurally re-tinted cap +
  shirt, no art files) and patrolling its own beat of the park at its own pace.
- **Controls:** arrow keys walk the player trainer (`heuristic`); **Tab** (or **T**) cycles which
  trainer is *selected*, and **walking the player up to another trainer selects it** — the selected
  trainer gets a gold `>name` tag and is the agent the **S** stats screen opens on (the top-right HUD
  shows `S: stats [<agent>]`). **S** = stats/radar screen (← → cycles agents there too), **H** = Hall
  of Fame, and stepping the player into a **gym** plays that ride and reveals the real score.

## Layout

```
web/
  index.html      # page shell; mounts the Kaplay canvas into #app
  src/
    main.js       # boots Kaplay, defines scenes, runs the world
    theme.js      # front-end mirror of the engine's park skin (lands, rides, palette) — presentation only
  package.json
```

## Art policy

**Original** GB/GBA-style pixel art, and/or **CC0 / permissively-licensed** tilesets only — never ripped
commercial assets (see [`../docs/11-visual-world.md`](../docs/11-visual-world.md)). Placeholder art now,
refined over laps.

## Screenshots

Every visual change commits a screenshot to `autoloop/shots/<timestamp>/` for async owner review (the
autoloop's Tier-B verification, [`../docs/10-autoloop.md`](../docs/10-autoloop.md)).
