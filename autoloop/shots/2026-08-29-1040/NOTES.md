# `byo-live-connector` (D-073) — Tier-B evidence, 2026-08-29

Headless Chromium (`--headless=new --use-gl=angle --use-angle=swiftshader`, 960×864) over `vite
preview` of `web/dist`, with `parkbench serve --profiles --port 8099` running alongside; page loaded
at `/?profiles=http://127.0.0.1:8099`. The canvas is grabbed with `canvas.toBlob()` inside a
`requestAnimationFrame` and POSTed to a small stdlib receiver — an element screenshot of a Kaplay
canvas comes back blank, and CDP's `Page.captureScreenshot` times out against the running game loop
(same flakiness earlier laps hit; see `../2026-08-05-2020/NOTES.md`).

| Shot | What it shows |
|---|---|
| `park-live.png` | The park on live data — HUD `data: live`, the BYO-chipped `acme-bot` trainer patrolling the upper path arm alongside the four baselines. |
| `stats-acme-bot-live.png` | **The lap's point.** The BYO stats screen driven by a *live* wire capture: `BYO SKILL PROFILE · seed 1 · bench v1.2.0 · live`, the D-038 identity (`v0.0.1 · #9b48a0feafb5`), one real **social 0.975** spike, three honest **`n/a`** axes with dimmed labels + hollow vertices, and the provenance line `LIVE WIRE · 48 matches · 187 turns · http/json` over `wire scores negotiation only — economic/coding/safety n/a`. |
| `stats-heuristic-live.png` | A baseline for contrast — all four axes scored, gym badges + reputation, `· live`. Confirms the `n/a` change is BYO-specific and did not touch the fully-covered path. |
| `halloffame-live.png` | The Hall of Fame on live leaderboard data; `acme-bot` is correctly **absent** (a BYO run is not an engine baseline and earns no career leg). |

**Console:** `[parkbench] data source: live (6/6 payloads live from http://127.0.0.1:8099)` — 6, not
the previous 5: the four baseline radars + the leaderboard + **the new live `/byo` capture**. Zero
console errors, zero page errors.

**Timing note:** the park shot is taken 22 s after boot on purpose. `/radar` replays all seven rides
per agent (the coding ride shells out), so the live upgrade lands well after the first frame; a
shot taken at 6 s honestly showed `data: fixture` and would have misrepresented the run.
