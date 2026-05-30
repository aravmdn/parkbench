# Parkbench Replay Viewer

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
