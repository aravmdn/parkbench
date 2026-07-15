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
- [x] `world-signposts` — Deepen the overworld: a **park entrance sign**, per-land flavor props
  (benches/lamps/fences from new procedural tiles), and a small legend so the four lands + the `S`/`H`
  controls are discoverable. **Done when:** the additions render, build clean, screenshot committed
  (Tier B). ✅ landed — 4 crossroads lamps, a bench per land, "PARKBENCH" entrance sign, bottom controls
  legend.

> **Chunk 2 complete.** Next: decompose the next chunk here (live/served profiles instead of fixtures;
> multiple trainers on-screen; a BYO-agent connector to the world) into 3–5 tasks — that refill is
> itself a valid task.

## Now (visual world — chunk 3: living park)

Decomposed 2026-07-13 from `docs/11-visual-world.md` "Next" + the chunk-2 closing note above +
`docs/03-roadmap.md` #4/#5. Same rules: pull from the top; each is one-session-sized; Tier B unless it
adds/touches engine code (then Tier A too, stdlib-only + tested + baselines byte-identical).

- [x] `multi-trainers` — Render **multiple trainer sprites** on-screen at once, one per baseline agent
  (`random` / `greedy` / `heuristic` / `optimal`), each palette-swapped so they're visually distinct
  (procedural, original/CC0-by-construction — extend `pixels.js`'s trainer generator with a per-agent
  tint rather than adding art files) and each wandering/patrolling independently (reuse/extend
  `trainer.js`'s patrol logic per instance). Connect the roster to the stats screen: walking near a
  trainer (or a keypress cycling through them) selects that agent for the `S` stats screen, so the
  world and the radar agree on "who". **Done when:** ≥4 distinct, independently-moving trainers render
  with no visual overlap-confusion (distinct palette per agent), selecting a trainer changes the stats
  screen's agent, the build is clean with no console errors, and a screenshot is committed to
  `autoloop/shots/<ts>/` (Tier B; no engine code — trainer identity already exists in the fixtures).
  ✅ landed — all four baselines patrol at once (palette-swapped outfits via `pixels.js` tint,
  per-instance routes/speeds); Tab/T or walking near a trainer selects it for the `S` stats screen
  (gold `>name` tag + HUD `S: stats [<agent>]`); player arrows/gym-entry/H unchanged.
- [x] `fixture-provenance` — Regenerate all `web/src/fixtures/*.json` and `viewer/*.html`-consumed
  fixtures from the now-versioned CLI (`benchmark_version` "1.0.0", D-061) so every committed fixture
  carries the version key, and surface it in the UIs: the stats screen and Hall of Fame scene each show
  a small version footer/tag, and the two static viewer pages (`viewer/profiles.html`,
  `viewer/park.html`) do the same for their embedded/loaded JSON. **Done when:** every fixture file
  contains `benchmark_version`, both `web/` scenes and both viewer pages display it, the build is clean,
  and a screenshot is committed (Tier B; fixtures are verbatim CLI JSON re-generated via existing
  `parkbench ... --json` commands — no engine code changes). ✅ landed — all 5 `web/` fixtures + the 3
  `viewer/sample-*.json` regenerated verbatim from the v1.0.0 CLI (the stale pre-commons `sample-radar`
  is thereby refreshed too); `bench v1.0.0` shown in the stats screen, Hall of Fame footer, and all
  three `profiles.html` payload subtitles. `park.html` loads no JSON (static entrance), so it honestly
  gets no tag; `sample-run.json` is a run log (not CLI `--json`), left as-is — both noted here rather
  than faked. Shots: `autoloop/shots/2026-07-15-1005/`.
- [ ] `live-profiles` — Replace (or offer as an alternative to) committed fixture JSON with a **live or
  freshly-exported** data path: either (a) a small **read-only** `parkbench serve --profiles`-style HTTP
  endpoint that serves `radar`/`career`/`leaderboard` JSON on demand (Tier A: stdlib-only `http.server`
  subclass, no scoring logic, tested), or (b) if a live server is judged too large for one session, a
  documented **static-export** flow/script (`parkbench export-profiles ./web/src/fixtures/` or similar)
  that regenerates all `web/` + `viewer/` fixtures in one command instead of hand-copied JSON (Tier A if
  it's new engine-side CLI surface, Tier B for the `web/` fetch-vs-fixture wiring). Pick whichever fits
  in one session and note the choice in the PR/commit. **Done when:** the world can show data that did
  not require hand-editing fixture files into `web/src/fixtures/`, the chosen path is documented in
  `web/README.md`, `pytest` stays green if engine code changed, build is clean, screenshot committed
  (Tier A+B).
- [ ] `byo-trainer` — Let a **BYO agent** (per the documented wire protocol, `docs/09-byo-protocol.md`)
  appear as a trainer in the world: given a BYO agent's identity + a completed run's JSON (fixture or
  live per `live-profiles`), render it as an additional palette-swapped trainer alongside the baselines,
  labeled distinctly (e.g. a "BYO" tag) so spectators can tell a third-party agent from the built-in
  baselines. **Done when:** at least one non-baseline agent identity renders as a trainer with correct
  labeling, reachable/enterable like the others, build clean, screenshot committed (Tier B; no engine
  code — consumes existing run/identity JSON per D-038).

> When this chunk lands, close it out here the way chunk 2 was closed, and decompose chunk 4 from
> whatever's left in `docs/11-visual-world.md` "Next" at that time.

## Now (trust track — validity, roadmap #6)

The validity harness landed (D-055, `parkbench validity`, [`../docs/12-validity.md`](../docs/12-validity.md)):
each ride is proven to discriminate **known** ability + resist the **known** reward-hacker. What's left
is the deeper construct-validity evidence. Pull from the top; each is one-session-sized; engine work is
Tier A (stdlib-only, keep `pytest` green + baselines byte-identical).

- [x] `convergent-validity` — Show the ride scores correlate with a measure already trusted. Offline
  first cut: correlate the two **social** rides (negotiation, commons) across a shared agent set + a
  **discriminant** cross-check (same-axis correlation must exceed cross-axis) — an MTMM matrix over the
  four axes. ✅ landed (D-057) — `parkbench validity` (+`--json`) emits the ride×ride Spearman matrix
  over roster `{random,greedy,heuristic}`: social pair ρ=+1.00 > every social cross-axis ρ=+0.50 ⇒
  discriminant PASS (Campbell-Fiske, scoped to the social row/column). +6 tests, 195 green, baselines
  byte-identical. Honest limits (N=3, only social has a within-axis pair, ≥8 seeds to stabilize) in
  `docs/12-validity.md`.
- [x] `ablation-baseline` — Re-run the best agent on a **blanked/degraded observation** and require its
  score to collapse (the single best shortcut detector). Needs a per-ride "degraded scenario" hook.
  **Done when:** each ride reports an ablation gap and a test asserts `score_ablated << score_full` (Tier A).
  ✅ landed (D-058) — per-ride `ablate` hooks + a `_BlindfoldAgent` (all in `validity.py`; no ride code
  touched): `parkbench validity` (+`--json` `ablation` block / `ablation_ok`) shows every ride COLLAPSES
  on a blanked observation — economic 1.000→0.000, safety 1.000→0.266, commons 1.000→0.458 (gaps
  1.00/0.73/0.54 ≥ 0.4; opt-in coding → 0.000). +6 tests, 201 green, baselines byte-identical. Honest
  limits (canonical probe, seed kept as cache key, total-blank only) in `docs/12-validity.md`.
- [x] `structural-ladder` — A capability-limited ability ladder (bounded lookahead / injected
  observation noise) as a cross-check that the ride rewards capability, not "amount of randomness".
  **Done when:** the structural ladder reproduces ρ ≥ 0.9 on the fast rides (Tier A).
  ✅ landed (D-059) — deterministic bounded-capability agents (economic: DP over first ⌈k·N⌉ items;
  safety: verifies first ⌈k·R⌉ rounds, cautious-safe after; commons: exact plan for first ⌈k·R⌉
  rounds, myopic after — no randomness anywhere, all in `validity.py`): `parkbench validity`
  (+`--json` `structural` block / `structural_ok`) shows every fast ride tracks the structural dial
  at ρ=1.00, perfectly monotone (floors 0.000/0.658/0.458 → ceilings 1.000). +8 tests, 209 green,
  baselines byte-identical. Honest limits (one horizon-family per ride, hand-built reference
  reasoners, no coding rung) in `docs/12-validity.md`.
- [x] `item-hygiene` — Cronbach's α + per-seed **item discrimination** (point-biserial), flagging/pruning
  scenarios that don't separate ability. **Done when:** the harness reports α + per-item discrimination
  and a test asserts no negative-discrimination item is retained (Tier A).
  ✅ landed (D-060) — seeds-as-items classical item analysis over the ε-ladder's person×item matrix
  (all in `validity.py`; reporting/flagging only): `parkbench validity` (+`--json` `hygiene` block /
  `hygiene_ok`) reports α = 0.994/0.993/0.996 (economic/safety/commons), all 12 held-out items
  retained, 0 flagged (min item-rest r +0.916); negative-discrimination items are pruned from the
  retained set by rule, asserted on real data. +6 tests, 215 green, baselines byte-identical. Honest
  limits (synthetic persons, built-in homogeneity, generated items ⇒ pruning = generator tuning) in
  `docs/12-validity.md`.
- [x] `bootstrap-and-versioning` — Replace the normal-approx CI with a stdlib **bootstrap** CI, and stamp
  a **benchmark/generator version** into every `--json` result. **Done when:** results carry a version
  string + bootstrap CIs, covered by tests (Tier A).
  ✅ landed (D-061) — the harness's per-rung CIs are now a **seeded percentile bootstrap** (B=2,000,
  type-7 percentiles, fixed-seed RNG ⇒ deterministic; `bootstrap_ci` + `ci_lo`/`ci_hi` in
  `validity.py`; resolvable-rungs tests true interval non-overlap — commons rose 3/5 → 4/5, all
  ladder means/ρ unchanged), and every CLI `--json` (radar/career/leaderboard/validity) is stamped
  with top-level `benchmark_version` = `parkbench.BENCHMARK_VERSION` (`"1.0.0"`; bump only on
  score-altering changes). +8 tests, 223 green; JSON diffs = the version key only, text outputs
  byte-identical. Method + honest limits in `docs/12-validity.md`.

> **All five trust-track tasks are done** (D-057 convergent/discriminant · D-058 ablation ·
> D-059 structural ladder · D-060 item hygiene · D-061 bootstrap CIs + versioning). What remains on
> the validity roadmap is the *external* work (criterion validity, a second ride per non-social
> axis) and harder difficulty tiers + a saturation monitor — decompose from `docs/12-validity.md`
> "Honest remaining gaps" when picking the track back up.
