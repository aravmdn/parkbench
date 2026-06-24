# Parkbench Viewers

Three static, dependency-free HTML pages. No build step, no server required — open any
file directly in any modern browser (modulo the `file://` fetch caveat noted below).

| File | What it shows |
|------|---------------|
| `park.html` | **Park map (start here)** — the themed entrance: every ride as an attraction, links to the viewers (D-046). |
| `index.html` | **Replay viewer** — step/auto-play through a negotiation `run.json` (`parkbench run`). |
| `profiles.html` | **Diagnostic profile viewer** — radar, career, and leaderboard payloads. |

---

# Park map (`park.html`)

The themed landing page (decision D-046) — the web face of the `parkbench map` command. It presents
every scored ride as an **attraction** grouped into the four **lands** (the skill axes, D-005), and
links to the replay and diagnostic viewers as the park's "souvenir booth". Pure static HTML/CSS/JS,
no fetch, no dependencies — `file://` works fine (double-click it). The attraction list **mirrors
`src/parkbench/theme.py`** (the static page can't import Python); the Python side is the source of
truth and is test-guarded against the ride registry, so keep the two in sync when adding a ride.

---

# Replay viewer (`index.html`)

A static, dependency-free HTML viewer for `run.json` files produced by `parkbench run`.
No build step, no server required — open `index.html` directly in any modern browser.

## How to open

```
viewer/
  index.html       ← open this in your browser
  sample-run.json  ← offline demo fixture (heuristic agent, seed 1, 48 matches)
```

**Option A — file://** (quickest)

1. Double-click `viewer/index.html`, or drag it into a browser tab.
2. Click **Load sample** to explore the bundled demo run, or click **Open run.json**
   to pick any run log from disk.

> Note: some browsers block `fetch()` on `file://` URLs, which means **Load sample**
> may not work when opened as a plain file. If that happens, use Option B or click
> **Open run.json** and pick `sample-run.json` manually — that always works.

**Option B — local server** (recommended for ?path= and Load sample)

```bash
# Python 3
python -m http.server 8080 --directory viewer/
# then open: http://localhost:8080
```

## How to load a run

| Method | When to use |
|--------|-------------|
| **Open run.json** button | Any run log from disk; works on file:// |
| **Load sample** button | Instantly loads the bundled demo |
| `?path=` query param | Pass a relative URL to a run.json served from the same origin: `http://localhost:8080?path=../runs/20260530-093433__heuristic/run.json` |

## Generating a new run.json

```bash
# Install the project (once)
uv venv && uv pip install -e ".[dev]"

# Run a suite and write a log to runs/
parkbench run --agent heuristic --seed 1
parkbench run --agent greedy    --seed 1
```

The CLI prints the path to the log file; open it with the viewer.

## What the viewer shows

- **Suite metadata** — name, seed, scenario/issue/level counts, round cap.
- **Agent profile** — overall efficiency, own value, deal rate with 95% CIs;
  per-persona breakdown with bar charts.
- **Match list** — all matches with deal/no-deal indicator and scores.
- **Transcript playback** — step forward/backward through turns (arrow keys or
  buttons), or auto-play at slow/normal/fast speed (spacebar toggles).
  Each turn shows the acting party, action type (offer/accept/message),
  message text, and offer levels.
- **Running score** — efficiency, own value, and the current offer on the table
  update as you step through the transcript; final scores lock in when a deal
  is reached.

---

# Diagnostic profile viewer (`profiles.html`)

A static, dependency-free viewer for the three diagnostic outputs Parkbench produces.
Open `profiles.html` directly, or serve the folder (same fetch caveat as above).

```
viewer/
  profiles.html            ← open this in your browser
  sample-radar.json        ← bundled demo: radar profile (heuristic, seed 1)
  sample-career.json       ← bundled demo: career / park tour (greedy, seed 1)
  sample-leaderboard.json  ← bundled demo: ranked careers (seed 1)
```

On first load (no `?path=`), it **auto-loads all three bundled samples** so the page is a
self-explanatory demo out of the box. Click **Open JSON** to load any one payload from disk —
the kind (radar / career / leaderboard) is **auto-detected** from its keys, so a single
button handles all three.

## What it shows

- **Radar** — a hand-drawn inline-SVG 4-axis spider chart (social · economic · coding · safety,
  each in `[0,1]`). Covered axes show their value; any axis in `missing_axes` is rendered as
  `n/a` with a hollow dashed marker — a **coverage gap, not a zero**. Below the chart, a
  per-ride breakdown lists each ride's score, sub-metrics, and flags any `integrity < 1`.
- **Career** — the "park tour": per-leg capability + integrity bars and the running `trust_after`
  (reputation), which **visibly collapses** on the leg where integrity drops. Headline equation
  **`career_score = mean_capability × reputation`** with all three numbers shown large.
- **Leaderboard** — a ranked table (rank, agent, career, capability, reputation, rides) plus an
  inline career-score bar chart. It **calls out the reward-hacker**: the economically strong
  agent that nonetheless ranks last because its reputation collapsed.

## How to load a payload

| Method | When to use |
|--------|-------------|
| **Open JSON** button | Any radar/career/leaderboard JSON from disk; works on `file://`; kind auto-detected |
| **Load samples** button | Re-loads the three bundled demos |
| `?path=` query param | Pass a relative URL to a payload served from the same origin: `http://localhost:8080/profiles.html?path=../runs/heuristic-radar.json` |

## Generating the fixtures

```bash
# Install the project (once)
uv venv && uv pip install -e ".[dev]"

# One command regenerates ALL committed spectator fixtures (these three samples + the
# web/src/fixtures/ set), byte-identical to the per-command invocations below:
parkbench export-profiles .   # run from the repo root

# Or one at a time:
# Radar (4-axis profile for one agent)
parkbench radar --agent heuristic --seed 1 --json > viewer/sample-radar.json

# Career (park tour — reputation compounding across rides)
parkbench career --agent greedy --seed 1 --json > viewer/sample-career.json

# Leaderboard (ranked careers across agents)
parkbench leaderboard --seed 1 --json > viewer/sample-leaderboard.json
```

(The viewer depends only on the JSON shape, not the invocation, so any seed/agent works.
`sample-run.json` is different — it is a run *log*, produced by `parkbench run`, not exported.)
