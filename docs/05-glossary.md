# 05 — Glossary

**Status:** Living · **Last updated:** 2026-05-30

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
- **Career / cross-ride coupling** — *(future, not in v1)* persistent reputation/resources that
  carry between rides so an agent's choices compound across a "run" of the park.
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
