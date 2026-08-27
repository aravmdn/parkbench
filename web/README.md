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
> spectator always knows which benchmark version produced the numbers on screen.

### Refreshing the fixtures

Never hand-edit the fixture JSON. Regenerate **every** `web/` + `viewer/` spectator fixture from the
versioned engine with one command (D-062), run from the repo root:

```sh
parkbench export-profiles          # (re)write every fixture from the current engine
parkbench export-profiles --check  # verify committed fixtures still match the CLI (drift → exit 1)
```

Each file is the **verbatim** `parkbench <cmd> --json` output (radar per baseline + the leaderboard for
`web/`, plus the `viewer/sample-*.json` samples), so provenance is automatic. `--check` is the standing
guard (`tests/test_export.py`): it fails if any committed fixture drifts from what the engine now emits,
so a stale fixture can't ship unnoticed. Comparison tolerates last-digit float-repr differences across
platforms, and files are written with canonical LF newlines. (`viewer/sample-run.json` is a run *log*,
not CLI `--json`, so it is intentionally left out; `viewer/park.html` loads no JSON.)

### Live data instead of fixtures (`serve --profiles`)

The committed fixtures are the **offline** data path. For **fresh** data without a regenerate-and-commit
step, run the read-only profiles endpoint (a stdlib `http.server`, presentation-only — it serves the
same producers' JSON the CLI does, with the `benchmark_version` stamp, and never computes a score):

```sh
parkbench serve --profiles --port 8080   # GET /radar?agent=… /career?agent=… /leaderboard /byo /health
```

Every response is the **verbatim** `parkbench <cmd> --json` output (byte-parity is pinned by
`tests/test_serve_profiles.py`), so it is a drop-in for the fixture files: `fetch('…/radar?agent=heuristic')`
gives the same JSON as `import`ing `src/fixtures/radar-heuristic.json`. Responses set
`Access-Control-Allow-Origin: *` so the Vite dev server (a different port) can fetch cross-origin.

**The world reads that endpoint** (D-069, `src/profiles.js`). Point the page at it with a `?profiles=`
query param:

| URL | What the world uses |
|---|---|
| `/` (no param) | **fixtures only — no network request is ever made** (the offline default) |
| `/?profiles=http://127.0.0.1:8080` | **live** JSON from that endpoint |
| `/?profiles=1` (`on`/`live`/`auto`/`yes`) | live from the default base `http://127.0.0.1:8080` |
| `/?profiles=0` (`off`/`fixture`) | fixtures only, explicitly |

So the usual live loop is:

```sh
parkbench serve --profiles --port 8080          # terminal 1 (from the repo root)
cd web && npm run dev                           # terminal 2
# open http://localhost:5173/?profiles=http://127.0.0.1:8080
```

How it behaves:

- **The world always boots on the fixtures first**, synchronously — live payloads are fetched after the
  first frames and swapped in when they land, so nothing ever waits on the network. Reachability is a
  **short `/health` probe** (2.5 s, `AbortController`); if it fails — server down, wrong port, wrong URL
  — the world simply stays on the fixtures. No hang, no blank screen, no thrown error.
- **The UI says which source it is showing**, next to the existing `bench vX.Y.Z` stamp: the stats
  screen subtitle and the Hall of Fame footer end in `· live` or `· fixture` (plus a `● LIVE` /
  `○ FIXTURE` chip in the corner), and the park HUD shows `data: live` / `data: fixture`. Tags are
  **per payload**, so a partial upgrade can never lie about the rest.
- The **BYO** trainer (`acme-bot`) is live too (D-073). It isn't on the engine's baseline roster, so it
  has its own route: `GET /byo` *plays a bring-your-own run over the negotiation wire on demand* and
  returns the completed profile. In live mode the BYO stats screen shows that real run; offline it
  falls back to the committed `radar-byo.json` like everything else. Because the v1 BYO wire carries
  **negotiation only** (`../docs/09-byo-protocol.md`), a live BYO profile honestly covers **one axis** —
  the other three draw as dimmed **`n/a`**, not as `0.000`, with the reason printed underneath.
- One honest wrinkle: if you *ask* for live data (`?profiles=…`) and the endpoint is **down**, the
  browser logs its own `net::ERR_CONNECTION_REFUSED` line for the failed probe. That is the browser's
  network log, not an app error (the app logs a single `console.info` saying it fell back). The plain
  no-param load stays completely clean because it makes no request at all.

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
- **Where the numbers came from** is always on screen: the HUD's `data: live` / `data: fixture`, and
  the matching tag on the stats screen + Hall of Fame (see the `serve --profiles` section above).

## Layout

```
web/
  index.html      # page shell; mounts the Kaplay canvas into #app
  src/
    main.js       # boots Kaplay, defines scenes, runs the world
    profiles.js   # the data source: live `serve --profiles` JSON when asked for, fixtures otherwise
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
