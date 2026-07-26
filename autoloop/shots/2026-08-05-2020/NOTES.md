# `web-fetch-profiles` (D-069) — Tier-B evidence, 2026-08-05

Headless Chromium (Playwright, `--use-gl=angle --use-angle=swiftshader`) over `vite preview` of
`web/dist`; canvas grabbed via `canvas.toDataURL()` inside a `requestAnimationFrame` (an element
screenshot of a Kaplay canvas comes back blank — that is the flakiness earlier laps hit).
Each `*-report.json` is the run's full console + network trace.

| Scenario | URL | What it shows |
|---|---|---|
| `live-*` | `?profiles=http://127.0.0.1:8099`, endpoint **up** (seed 1) | live radar + Hall of Fame; `· live` tags, `● LIVE` chip, HUD `data: live`; 5/5 payloads live, 0 console errors |
| `live-seed7-*` | same, endpoint run with `--seed 7` | **seed 7** numbers (social 0.970 / economic 0.983) that exist in no committed fixture — proof the pixels came from the endpoint |
| `fixture-*` | `/` (no param), endpoint up | offline default: **zero** network requests, fixtures, `· fixture` tags |
| `fallback-*` | `?profiles=http://127.0.0.1:8099`, endpoint **killed** | same world, fixture fallback, no hang; the one console line is the *browser's* `net::ERR_CONNECTION_REFUSED` for the failed probe, not an app error (`pageErrors: []`) |
