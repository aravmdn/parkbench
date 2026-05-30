# 06 — v1 Core Architecture

**Status:** Stable · **Last updated:** 2026-05-30

How the v1 negotiation ride is implemented. This started as the "core" slice (decision D-026): the
engine, scenario generator, scoring, scripted house cast, baseline/heuristic agents, and a CLI. The
**HTTP/JSON server** for external BYO agents is now built on top of it (D-027 — see
[The HTTP/JSON server](#the-httpjson-server-d-027)). The replay viewer, nudge controls, and a real
LLM agent remain deferred (see [`04-open-questions.md`](04-open-questions.md)).

## Module map — `src/parkbench/`

| Module | Responsibility |
|---|---|
| `protocol.py` | `Observation`, `Action` (message/offer/accept), `Offer` — the JSON wire contract (D-015), passed in-process for now. An `Observation` carries only the acting agent's **own** utilities (D-016). |
| `scenario.py` | `Scenario` (the utility model), `generate_scenario(seed)` (seeded, integrative), and `analyze()` (brute-forces the welfare/Nash/Pareto optima). |
| `engine.py` | `run_match()` — the turn-based loop with a round cap (D-017). |
| `agents/base.py` | `Agent` ABC; `reset(seed, total_rounds)` re-seeds the RNG (this is what makes suites reproducible). |
| `agents/conceder.py` | `ConcederStrategy` — the shared time-based concession + logrolling strategy used by the heuristic agent and every persona. |
| `agents/baselines.py` | `RandomAgent` (floor) and `GreedyAgent` (selfish, never concedes). |
| `agents/heuristic.py` | `HeuristicNegotiator` — the "good" stand-in test agent (no LLM key needed). |
| `agents/llm.py` | `Provider` interface + `LLMAgent` stub — the BYO/LLM seam (D-025), intentionally unimplemented. |
| `personas/house_cast.py` | The four scripted personas: `Tough`, `Fair`, `Cooperative`, `Slippery` (D-024). |
| `scoring.py` | `score_match()` (efficiency + own-value), `Stat` (mean/std/CI95), `build_profile()`. |
| `suite.py` | `Suite` (seed + counts) and `run_suite()` — agent × every persona × every scenario. |
| `runlog.py` | Writes a JSON run log (profile + per-match transcripts) to `runs/` — the replay viewer's input. |
| `server.py` | The park-hosted HTTP/JSON server (D-027): an `HttpBridgeAgent` (side-A stub that blocks on the network) + a stdlib `ThreadingHTTPServer`. Hosts one run, drives it via `run_suite`, writes the same run log. |
| `client.py` | `drive_agent(base_url, agent)` — a reference `urllib` poll-loop adapter that serves any local `Agent` to a `ParkServer` over the wire (the BYO example). |
| `cli.py` | `parkbench run`, `parkbench analyze`, and `parkbench serve`. |

## Utility model (D-016)

Each scenario has `N` issues, each with `L` discrete levels `0..L-1`. Party **A** (the test agent)
prefers high levels; party **B** (the house persona) prefers low levels:

```
u_A(outcome) = Σ_i  w^A_i · ( l_i / (L-1) )
u_B(outcome) = Σ_i  w^B_i · ( 1 − l_i / (L-1) )
```

Each party's weights sum to 100, so each party's best possible payoff is 100. Weights are
**anti-correlated** across parties (A's least-valued issue is B's most-valued), which guarantees
value-creating trades exist — conceding an issue you weight lightly hands it to a counterpart who
weights it heavily (logrolling).

Because joint payoff per issue is linear in the level, the welfare-maximizing agreement gives each
issue to whichever party weights it more:

```
max_joint = Σ_i  max( w^A_i , w^B_i )
```

`analyze()` brute-forces all `L^N` outcomes (default `3^4 = 81`) for `max_joint`, each party's best,
the Nash bargaining solution (argmax `u_A·u_B`, disagreement = 0), and the Pareto frontier.

## Scoring (D-019)

Two metrics per match, both in `[0, 1]`, both `0` on no-deal:

```
efficiency = ( u_A + u_B ) / max_joint     # "joint value captured": were the trades found?
own_value  =   u_A / max_A                 # "own share": how much A captured for itself
```

A suite reports each metric's **mean, sample std, and 95% CI** (`1.96·std/√n`). The CI/variance is
the evidence for the reproducibility claim (D-020).

## Determinism

Scripted cast + seeded scenario generation + deterministic agents ⇒ identical results for a given
suite seed. `run_suite()` seeds every agent per match from the suite seed (`agents[].reset(seed,
total_rounds)`); `RandomAgent` and the `Slippery` persona draw only from that seeded RNG. The
`tests/test_determinism.py::test_*reproducible` tests assert byte-identical profiles across runs.

## The fixed suite (D-020)

`suites/v1_negotiation.json` is the canonical spec; the CLI mirrors it: **seed 1, 12 scenarios,
4 issues × 3 levels, round cap 8, 4 personas → 48 matches.** Scenarios are generated from seeds
`seed .. seed+11`.

## Agents & personas

| Name | Kind | Behavior |
|---|---|---|
| `random` | baseline / floor | Random offers; accepts ~25% of the time. |
| `greedy` | baseline | Always demands its own best; never concedes; rarely closes. |
| `heuristic` | test (good) | Time-based concession; concedes cheap issues first (logrolling). |
| `tough` / `fair` / `cooperative` / `slippery` | house cast | One `ConcederStrategy` tuned to four dispositions; `slippery` adds RNG noise. |

## The HTTP/JSON server (D-027)

The wire realisation of D-015, so a **bring-your-own** agent can be scored over HTTP without bespoke
glue. It is **park-hosted and agent-polled**, **stdlib only** (no new dependencies, upholds D-023),
and reuses `protocol.py`, `engine.py`/`suite.py`, and `runlog.py` **unchanged** (the run-log schema
is untouched, so the viewer/nudge slices are unaffected).

- The park runs `run_suite` in a background thread. Side A is an `HttpBridgeAgent` whose `act(obs)`
  publishes the observation and **blocks** until the external agent posts an action. The house side
  (B) never goes over the wire, so the park keeps full control of the loop and stays deterministic.
- The external agent is a pure HTTP **client** — no inbound server needed on its side:

  | Endpoint | Returns |
  |---|---|
  | `GET /observation` | `{"status":"your_turn","turn":N,"observation":{…}}` when it's the agent's turn (with a `new_match` field carrying `seed`/`total_rounds` on a match's first turn); else `{"status":"waiting"}`; or `{"status":"done","profile":{…}}` when the run is over. |
  | `POST /action` | body is an `Action`-shaped JSON object (`{type, offer, message}`); replies `{"status":"accepted","turn":N}`, or `409` if it isn't the agent's turn. |
  | `GET /health` | `{"status":"ok","agent":"<name>"}`. |

- **Determinism parity.** `run_suite` re-seeds side A per match; the park forwards that match's
  `seed`/`total_rounds` to the client (`new_match`) so a seed-dependent BYO agent re-seeds
  identically. `tests/test_server.py` spins the server up in-process on an ephemeral port, drives a
  local heuristic (and a seed-dependent random) agent end-to-end over HTTP, and asserts the profile
  is **byte-identical** to the pure in-process run. No external network.
- `client.drive_agent(base_url, agent)` is the small in-process adapter that serves any existing
  `Agent` over the wire — both the reference BYO example and the test harness.

## How to run

```bash
uv venv && uv pip install -e ".[dev]"      # or: python -m venv .venv && pip install -e ".[dev]"
pytest                                      # 21 tests (14 core + 7 HTTP server)
parkbench run --agent heuristic --seed 1    # run the suite, print a profile, write a run log
parkbench run --agent greedy --seed 1       # compare a weaker strategy
parkbench analyze --seed 1                  # inspect one scenario's optimum
parkbench serve --port 8080                 # host a run over HTTP for an external BYO agent (side A)
parkbench serve --port 0 --local-agent heuristic   # self-drive a built-in agent over HTTP (demo/test)
```

## Results snapshot (seed 1, 48 matches)

| Agent | Efficiency (mean ± CI95) | Own value | Deal rate |
|---|---|---|---|
| `heuristic` | 0.978 ± 0.012 | 0.638 ± 0.030 | 100% |
| `random` (floor) | 0.840 ± 0.039 | 0.443 ± 0.063 | 100% |
| `greedy` | 0.412 ± 0.129 | 0.426 ± 0.132 | 46% |

Clean separation across three strategies, tight CIs for consistent play (heuristic) vs. wide for
erratic play (greedy), and a working per-persona signal (the heuristic captures more vs. `cooperative`
than vs. `tough`). This satisfies the v1 success criteria in [`01-v1-scope.md`](01-v1-scope.md):
**discrimination** + **reproducibility**.

## Deferred

The static replay viewer, nudge controls, and a real LLM reference agent — tracked in
[`04-open-questions.md`](04-open-questions.md). (The HTTP/JSON server is now built — D-027 above.)
