# 06 — v1 Core Architecture

**Status:** Stable · **Last updated:** 2026-05-30

How the v1 negotiation ride is implemented. It began as the "core" slice (decision D-026): the
engine, scenario generator, scoring, scripted house cast, baseline/heuristic agents, and a CLI.
Built on top since: the **HTTP/JSON server** for external BYO agents (D-027), a **static replay
viewer** over the run logs (D-028), **nudge controls** with off-record flagging (D-029), and a real
**LLM reference agent** via OpenRouter (D-030); the personas and scenario suite were also tuned for
sharper discrimination (D-031/D-032).

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
| `agents/llm.py` | `Provider` interface + `OpenRouterProvider` (stdlib-only) + `LLMAgent` — the real LLM reference agent (D-030, refines D-025); falls back to the heuristic on any failure. |
| `personas/house_cast.py` | The four scripted personas: `Tough`, `Fair`, `Cooperative`, `Slippery` (D-024). |
| `scoring.py` | `score_match()` (efficiency + own-value), `Stat` (mean/std/CI95), `build_profile()`. |
| `suite.py` | `Suite` (seed + counts) and `run_suite(suite, agent, nudge=None)` — agent × every persona × every scenario; a `Nudge` restricts the roster / injects a scenario and flags the run off-record. |
| `runlog.py` | Writes a JSON run log (profile + per-match transcripts) to `runs/` — the replay viewer's input. Versioned (`schema_version`) with a top-level `off_record` flag (D-029) and a top-level `agent` identity block (D-038). |
| `nudge.py` | `Nudge` spec, the persona-name registry, and `parse_scenario_spec()` (inline JSON or file). Powers the observe+nudge loop (D-029); keeps CLI/suite edits localized. |
| `server.py` | The park-hosted HTTP/JSON server (D-027): an `HttpBridgeAgent` (side-A stub that blocks on the network) + a stdlib `ThreadingHTTPServer`. Hosts one run, drives it via `run_suite`, writes the same run log. |
| `client.py` | `drive_agent(base_url, agent)` — a reference `urllib` poll-loop adapter that serves any local `Agent` to a `ParkServer` over the wire (the BYO example). |
| `cli.py` | `parkbench run` (incl. `--swap-persona`, `--inject-scenario`, `--off-record`), `parkbench analyze`, and `parkbench serve`. |
| `dotenv.py` | A zero-dep `.env` loader the CLI calls at startup (D-033); real env vars take precedence. |

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
round cap 8, 4 personas → 48 matches.** Scenario shapes **vary** across the suite (3–5 issues ×
3–5 levels, cycled from a fixed `SCENARIO_SHAPES` menu; `Suite.vary_shapes=True` by default) and
per-issue weights are moderately dispersed (D-032). Scenarios are generated from seeds
`seed .. seed+11`.

## Nudge controls + off-record (D-029)

The observe+nudge loop (D-003, D-021) is realized as a `Nudge` passed to `run_suite`:

- **`--swap-persona <name>`** — face only the named counterpart (`tough`/`fair`/`cooperative`/
  `slippery`) instead of the whole roster. Names resolve via `nudge.PERSONA_REGISTRY`.
- **`--inject-scenario <JSON|PATH>`** — run a single human-supplied scenario instead of the seeded
  suite scenarios. Accepts inline JSON or a path to a `.json` file; parsed by `parse_scenario_spec`
  into a `Scenario` (fields: `weight_a`, `weight_b` required; `issues`, `n_levels`, `seed` optional).
- **`--off-record`** — force off-record without swapping/injecting.

**Off-record is enforced, not advisory.** Using swap or inject auto-sets `off_record=True`.
`scoring.build_profile` aggregates **only on-record matches** into the canonical profile and records
the dropped count as `Profile.excluded`; nudged runs are aggregated separately by
`build_off_record_profile` (which sets `Profile.off_record=True`). So an off-record match can never
move a canonical mean, std, CI, deal-rate, or per-persona figure — the exclusion is by construction.

## Run-log schema (`runs/<ts>__<agent>[__off_record]/run.json`)

The log is **versioned** so the server/replay slices can detect shape changes. Every bump is
**additive** — **all pre-existing fields are unchanged and in their original positions**. D-029 set
`schema_version = 2` (added `schema_version` + the `off_record` flags); **D-038** sets
`schema_version = 3`, adding a top-level **`agent` identity block** `{name, version, config_hash}`
(see D-038 / [`07-multi-ride.md`](07-multi-ride.md)). Fields by version:

| Field | Type | Location | Added | Meaning |
|---|---|---|---|---|
| `schema_version` | `int` | top level | D-029 | Run-log schema version (currently `3`). Absent ⇒ treat as `1`. |
| `off_record` | `bool` | top level | D-029 | Whether the whole run was nudged/off-record (default `false`). |
| `off_record` | `bool` | each entry of `matches[]` (appended last) | D-029 | Per-match off-record flag (mirrors the run flag in v1). |
| `agent` | `object` `{name: str, version: str, config_hash: str}` | top level (between `off_record` and `suite`) | D-038 | The acting agent's stable identity (D-038): `name`, `version` (defaults to the package version, else `"0"`), and a short deterministic `config_hash` of its defining config. |

`write_run` stamps the `agent` block from the agent's `identity()` when the caller passes
`agent=`; when omitted (older call sites) it is derived from the profile's agent name with version
`"0"`, so the field is always present. The CLI and HTTP server both pass the agent through.

Existing top-level keys remain `suite`, `profile`, `matches`; existing per-match keys
(`scenario_seed`, `n_issues`, `n_levels`, `persona`, `agreed`, `outcome`, `efficiency`, `own_value`,
`turns_used`, `transcript`, `analysis`) are untouched (`n_issues`/`n_levels` log the per-scenario
shape, which varies under D-032). Off-record runs also get a `__off_record` directory suffix.

## Agents & personas

| Name | Kind | Behavior |
|---|---|---|
| `random` | baseline / floor | Random offers; accepts ~25% of the time. |
| `greedy` | baseline | Always demands its own best; never concedes; rarely closes. |
| `heuristic` | test (good) | Time-based concession; concedes cheap issues first (logrolling). |
| `tough` / `fair` / `cooperative` / `slippery` | house cast | Each gates acceptance with an explicit, time-relaxing **reservation floor** (tough highest → cooperative lowest; `slippery` adds RNG noise) layered over the shared `ConcederStrategy` proposal logic (D-031). |
| `llm` | test (reference) | A real LLM negotiator via OpenRouter (D-030). Falls back to `heuristic` on any failure. |

## The LLM reference agent (D-030)

`agents/llm.py` wires a real LLM negotiator using **only the standard library**
(`urllib.request` + `json`) — no third-party SDK and no new runtime dependency (D-023).

- **`Provider`** is the adapter seam (`complete(messages, **opts) -> str`).
- **`OpenRouterProvider`** POSTs to OpenRouter's OpenAI-compatible endpoint
  `https://openrouter.ai/api/v1/chat/completions` with a short HTTP timeout (20 s).
- **`LLMAgent.act`** builds a compact prompt from the Observation — using **only the
  agent's own** payoff table, the standing offer, `rounds_left`, and recent history
  (private preferences, D-016) — and instructs the model to reply with **only** a JSON
  object: `{"type":"offer"|"accept"|"message","levels":[...],"message":"..."}`. That JSON
  is parsed and validated into a `protocol.Action` (offers must have one in-range integer
  level per issue).
- **Graceful degradation, transparently (D-030, hardened):** on *any* missing key / network /
  timeout / parse / validation error it falls back to the deterministic `HeuristicNegotiator`
  move, so a run never crashes or hangs, and it logs **nothing to stdout** (scores + run log stay
  byte-identical). Because a silent fallback would let a keyless run print heuristic numbers under
  the `llm` label — a trust footgun — the agent also tracks `live_calls` / `fallback_calls`
  (and `used_live_llm`) and, when it built its own **keyless** provider, prints a **one-time
  stderr notice** that the run is a fallback, not a live LLM. An *injected* provider (e.g. in tests)
  is assumed intentional and never triggers the notice.

### Running it live

A live run needs **both** an API key **and** outbound network egress to the provider:

```sh
export OPENROUTER_API_KEY=sk-...
parkbench run --agent llm --seed 1        # stderr stays quiet ⇒ it really called the model
```

If `OPENROUTER_API_KEY` is unset you'll see the one-time stderr fallback notice above. Note that a
**sandboxed environment may block egress** to `openrouter.ai` at the network-policy layer (e.g. the
cloud build environment denies it with a proxy `403`); there the `llm` agent falls back regardless of
the key. Run live agents where the provider host is reachable, or point `OPENROUTER_MODEL` /
`OpenRouterProvider(url=...)` at an allowed endpoint. The key is a secret: keep it in a **gitignored
`.env`** (auto-loaded, D-033) or the environment — never commit it, and it is deliberately excluded
from the agent's identity hash (D-038).

### Environment variables

| Var | Required | Default | Purpose |
|---|---|---|---|
| `OPENROUTER_API_KEY` | for live LLM calls | — (absent ⇒ heuristic fallback) | OpenRouter API key. |
| `OPENROUTER_MODEL` | no | `DEFAULT_MODEL` in `agents/llm.py` (a `:free` model id) | Override the model. |

The default model is the `DEFAULT_MODEL` module constant in `src/parkbench/agents/llm.py`
(a free model id ending in `:free`); change it there or via `OPENROUTER_MODEL`.

The CLI **auto-loads a `.env`** from the working directory at startup (D-033), so dropping
`OPENROUTER_API_KEY=…` (and optionally `OPENROUTER_MODEL=…`) in a local `.env` is enough — no manual
`export` needed. Real environment variables (and CI secrets) override the file.

### Run a live negotiation

```bash
export OPENROUTER_API_KEY=sk-or-...          # PowerShell: $env:OPENROUTER_API_KEY="sk-or-..."
# optional: export OPENROUTER_MODEL="vendor/model:free"
parkbench run --agent llm --seed 1           # the LLM plays every persona × scenario
```

Without `OPENROUTER_API_KEY` the same command still runs end-to-end, falling back to the
heuristic move on every turn.

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

## Replay viewer (D-028)

`viewer/index.html` is a single static file — no build step, no dependencies, opens directly via
`file://` — that renders any `run.json`. Load a run with the file picker or a `?path=` query param;
it shows the suite header, the agent profile + per-persona bars, the match list, and per-match
transcript **playback** with the running score updating as offers land and lock in on accept. It
reads the existing run-log schema (no server needed); `viewer/sample-run.json` is an offline demo
fixture and `viewer/README.md` documents usage.

## How to run

```bash
uv venv && uv pip install -e ".[dev]"      # or: python -m venv .venv && pip install -e ".[dev]"
pytest                                      # 57 tests
parkbench run --agent heuristic --seed 1    # run the suite, print a profile, write a run log
parkbench run --agent greedy --seed 1       # compare a weaker strategy
parkbench analyze --seed 1                  # inspect one scenario's optimum
parkbench serve --port 8080                 # host a run over HTTP for an external BYO agent (side A)
parkbench serve --port 0 --local-agent heuristic   # self-drive a built-in agent over HTTP (demo/test)

# Nudge controls (D-029) — these runs are off-record and excluded from canonical scores:
parkbench run --agent heuristic --swap-persona tough            # face only the tough persona
parkbench run --agent heuristic --inject-scenario scn.json      # run a supplied scenario (or inline JSON)
parkbench run --agent heuristic --off-record                    # force off-record without nudging
```

## Results snapshot (seed 1, 48 matches)

| Agent | Efficiency (mean ± CI95) | Own value | Deal rate |
|---|---|---|---|
| `heuristic` | 0.975 ± 0.009 | 0.548 ± 0.047 | 100% |
| `random` (floor) | 0.881 ± 0.044 | 0.336 ± 0.051 | 98% |
| `greedy` | 0.100 ± 0.076 | 0.125 ± 0.095 | 12.5% |

Clean separation across three strategies (efficiency 0.975 > 0.881 > 0.100), tight CIs for
consistent play (heuristic) vs. wide for erratic play. After the D-031 reservation floors the
**per-persona signal is crisp**: heuristic own-value spreads `cooperative` 0.772 → `fair` 0.554 →
`slippery` 0.511 → `tough` 0.356 with non-overlapping CI95s, and `greedy` now correctly collapses
against the stiffer floors (12.5% deal rate). This satisfies the v1 success criteria in
[`01-v1-scope.md`](01-v1-scope.md): **discrimination** + **reproducibility**.

## Deferred

The four v1 follow-ups are now built: the HTTP/JSON server (D-027), the static replay viewer
(D-028), nudge controls (D-029), and the LLM reference agent (D-030). Remaining work is
cross-cutting / post-v1 — tracked in [`04-open-questions.md`](04-open-questions.md).
