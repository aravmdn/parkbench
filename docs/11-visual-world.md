# 11 — The Visual World (Pokémon-style spectator park)

**Status:** Draft · **Last updated:** 2026-07-13

This is the **front-of-house** vision (D-050). The **behind-the-scenes** is the benchmark engine you
already have — rides are scored capability tests, with a deterministic radar/career/leaderboard. The
front-of-house is an **animated, Game Boy / GBA-era pixel world**: a vibrant theme park where each
agent is a **trainer character** who walks the park and steps into attractions to "ride" them. The
visuals are a real little game; the scores are the benchmark running underneath. It is the evolution of
the static park skin (D-046) into a living world.

> **Load-bearing rule (upholds D-012):** the visual world is **presentation only**. It never computes
> or influences a score. It *reads* the engine's outputs and draws them. All truth stays in the engine.

## The mapping (metaphor → engine)

| Pokémon-world element | Parkbench meaning |
|---|---|
| The overworld map | The park |
| Towns / routes / regions | The **lands** = the four axes (social · economic · coding · safety), per `theme.py` (D-046) |
| Buildings / **gyms** you enter | The **rides** — entering a gym = an agent attempting that ride/benchmark |
| **Trainer sprites** (4-direction walk cycles) | The **agents** (`heuristic`, `greedy`, `random`, `optimal`, `llm`, BYO…) |
| A trainer walking to a gym and going in | A **run** — the match plays out, the trainer exits with a result |
| The **stats screen** (hex radar) | The **radar profile** (`radar --json`) |
| **Gym badges** earned | The **career / reputation** (badges revoked for a reward-hacker whose reputation collapsed) |
| **Hall of Fame** | The **leaderboard** (`leaderboard --json`) |

The metaphor is a near 1:1 with the engine — that's why it's worth doing properly rather than as chrome.

## Architecture — the engine ↔ front-end split (D-050)

- **Engine (unchanged contract):** Python, **stdlib-only**, pure, deterministic, fully test-gated
  (D-023). It already emits everything the world needs as JSON — `parkbench radar --json`,
  `career --json`, `leaderboard --json`, and the run logs. This is the same contract the static viewers
  consume (D-028/D-044).
- **Front-end (new, its own app):** lives in **`web/`** as a **separate application** that **is allowed
  dependencies and a build step** (the stdlib-only rule is an *engine* rule; it does not bind the
  front-end). It consumes the engine's JSON and renders the world. No scoring logic ever lives here.
- **Data flow:** engine → JSON → `web/` reads it. During development the loop can generate fixture JSON
  (e.g. from the seeded baselines) into `web/` so the world has something to render offline. Those
  fixtures are no longer hand-copied: **`parkbench export-profiles`** (D-062) regenerates every
  `web/` + `viewer/` fixture from the versioned CLI in one command, and `parkbench export-profiles
  --check` is a standing provenance guard that fails if any committed fixture drifts from the engine.

## Stack

- **Kaplay** (the maintained fork of Kaboom.js) — purpose-built for exactly this: pixel sprites,
  animation frames, tilemap levels (`addLevel`), scenes. Tiny footprint, minimal boilerplate, so effort
  goes into *the world*, not into re-inventing a 2D engine.
- **Fallback:** Phaser 3 (+ Tiled) if we later need heavier tilemap tooling or physics. The autoloop may
  revisit this in its first scaffolding lap and log the choice as a decision.

## Art policy

- **Original** GB/GBA-style pixel art, and/or **CC0 / permissively-licensed** open tilesets. **Never
  ripped Nintendo/Pokémon assets** — this product must be trustworthy and publishable, so third-party IP
  is out. Start with rough placeholder art and refine over laps.
- Commissioning or upgrading to higher-quality art is a later call, parked in
  [`04-open-questions.md`](04-open-questions.md).

## Verification (why this needs the autoloop's special rule)

There is **no `pytest` oracle for "does the town look right."** So the autoloop charter
([`10-autoloop.md`](10-autoloop.md)) requires every **visual** lap to run the world (headless or via
Claude-in-Chrome) and commit **screenshots** into `autoloop/shots/<timestamp>/` so the owner reviews
the look **asynchronously** and can revert anything off-vision. Engine laps keep the strict tests-green
bar; visual laps add the build-succeeds + screenshots-committed bar.

## Status & first steps (for the loop)

**Seed laps built (D-053, 2026-07-03).** `web/` is scaffolded (Kaplay + Vite) and the six seed tasks
have landed: the overworld tilemap, the four labeled lands, a gym per ride, a walking 4-direction
trainer (arrow-key + auto-patrol), and the stats screen — an agent's four-axis radar rendered from
verbatim `parkbench radar --json` fixtures, reachable with `S` and cycled with ← →. All art is
procedurally generated (`web/src/pixels.js`, original/CC0), and the front-end stays presentation-only
(D-012) — no engine code changed. Screenshots for each lap are under `autoloop/shots/`.

**Chunk 2 landed (2026-07-03–07):** the **Hall of Fame** scene (`leaderboard --json`, reachable with
`H`), **badge/reputation** visuals on the stats screen (earned vs. cracked gym badges from `career`/
`leaderboard` `legs`), the headline **"trainer enters gym → run plays → result"** flow, and
**world-signposts** (entrance sign, per-land props, a controls legend). See `autoloop/backlog.md`
("visual world — chunk 2: spectator payoffs") for the landed task records.

**Chunk 3 decomposed (2026-07-13):** into `autoloop/backlog.md` ("visual world — chunk 3: living
park") — `multi-trainers` (one palette-swapped trainer per baseline agent, roster tied to the stats
screen's agent selection), `fixture-provenance` (regenerate fixtures with the now-versioned CLI,
D-061's `benchmark_version`, and surface it in the `web/` scenes + `viewer/` pages), `live-profiles`
(a live read-only profiles endpoint or a one-command static-export flow, replacing hand-copied
fixture JSON), and `byo-trainer` (a third-party BYO agent rendered as a labeled trainer). Pull tasks
from the top of the backlog; keep this doc updated as the chunk lands.

**Chunk 3 COMPLETE (2026-07-22).** `multi-trainers` + `fixture-provenance` landed (2026-07-13→15);
`live-profiles` landed 2026-07-22 as the **static-export flow** (D-062, `parkbench export-profiles` —
the live HTTP endpoint variant is deferred to `docs/04-open-questions.md`); and `byo-trainer` landed
2026-07-22 (**D-063**) — a third-party BYO agent (`acme-bot`) renders as a "BYO"-chipped, palette-swapped
trainer alongside the four baselines, selectable (Tab / walk-up) and driving the `S` stats screen, which
surfaces its D-038 identity where a baseline shows reputation + badges. Presentation-only (D-012); its
`radar-byo.json` stand-in sits outside `export-profiles`' manifest (a BYO run is not an engine baseline).
**Next:** decompose **chunk 4** from this doc's "Next" — live/served profiles (the deferred
`serve --profiles` endpoint), richer per-land art, and a BYO-over-the-wire connector that renders a
*live* third-party run rather than a fixture.
