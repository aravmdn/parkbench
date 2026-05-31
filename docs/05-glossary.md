# 05 — Glossary

**Status:** Living · **Last updated:** 2026-05-31

Shared vocabulary for the project. Keep terms here so docs can link to a single definition.

- **Park** — the whole benchmark arena; the collection of rides plus the scoring/observation layer.
- **Ride** — a single self-contained, scored attraction that tests one capability. The unit of the
  benchmark. (See [`00-vision.md`](00-vision.md).)
- **Skill axis** — one of the four capability dimensions measured: **Social**, **Economic**,
  **Coding/Tools**, **Safety/Robustness**. These are also the axes of the output radar chart.
- **Radar profile / skill profile** — the headline output for an agent: a per-axis (and per-ride)
  diagnostic of strengths and weaknesses, rather than a single rank.
- **House cast** — the fixed set of agents/personas the project controls. They populate multi-agent
  rides as standardized counterparties/society. Because they are fixed, they make multi-agent rides
  **reproducible** — they are scoring infrastructure, not decoration.
- **BYO agent ("bring-your-own")** — an externally supplied agent connected over the published
  protocol; the agent **under test** in a run.
- **Test agent** — the specific agent being scored in a given run (house or BYO).
- **Observe + nudge** — the human role: watching runs (dashboards/replays/profiles) and intervening
  (coaching agents, injecting events/scenarios). Nudging also serves as an adversarial-robustness
  probe.
- **Objective payoff scoring** — scoring by measurable outcome (value captured / goal achieved),
  normalized against baseline reference agents. The v1 scoring backbone.
- **Baseline / reference agent** — a known agent used to normalize scores so results are comparable
  and discriminating.
- **Career / cross-ride coupling** — the first coupling between rides (D-041): an agent's standing
  across a whole "run" of the park. **`career_score = mean_capability × reputation`** — capability
  (mean ride score) discounted by reputation, so misconduct anywhere lowers the whole career.
  Implemented in `parkbench career`; deliberately reverses part of "independent rides" (D-008).
- **Integrity (signal)** — a per-ride number in `[0, 1]` declared in a `RideResult.detail` saying
  whether the agent stayed within that ride's hard rules: safety = non-violation rate, economic =
  feasibility (budget) rate, coding = compile rate, social = neutral (1.0). The raw material of
  reputation (D-041).
- **Reputation** — accumulated trust across the career: the **product** of every ride's integrity
  signal. Multiplicative, so it is hard to earn (every ride clean) and easy to lose (one ride
  dirty); a single serious breach dominates (D-041).
- **Leaderboard** — a ranking of agents by career score (`parkbench leaderboard`, D-042); the first
  watchable spectator surface (roadmap #4).
- **Solo ride vs. multi-agent ride** — a ride scored with one agent in isolation vs. one where
  multiple agents interact and scores depend on the interaction.
- **Nudge** — a human intervention on a run: injecting a chosen scenario or swapping the counterpart
  persona (D-029).
- **Off-record** — a run flagged as nudged (or forced with `--off-record`); **excluded by
  construction** from canonical profiles so it can't move a real score, and aggregated separately.
- **Reservation floor** — the minimum share of its own maximum a house persona will accept; relaxes
  over the rounds. Distinct floors per persona make per-persona outcomes distinguishable (D-031).
- **Wire protocol (HTTP/JSON)** — the park-hosted, agent-polled HTTP API a BYO agent uses to be
  scored over the network: `GET /observation`, `POST /action` (D-015 / D-027).
- **Run log** — the per-run `run.json` (suite + profile + per-match transcripts) written to `runs/`;
  the replay viewer's input. Versioned via `schema_version` (D-029).
- **Subprocess-isolated harness** — the coding ride runs untrusted candidate code in a separate,
  wall-clock-time-bounded Python process (D-043) so a hanging/crashing/malicious candidate just fails
  (score 0) instead of freezing or compromising the ride. Process isolation + a timeout — **not** a
  full OS sandbox (no filesystem/network/resource confinement yet).
- **Diagnostic-profile viewer** — `viewer/profiles.html` (D-044): a static, zero-dependency page that
  renders the radar (inline-SVG), career (trust-collapse), and leaderboard (reward-hacker callout)
  from the `radar`/`career`/`leaderboard --json` outputs. Sibling to the negotiation replay viewer
  (`index.html`, D-028).
