# 06 — v1 Core Architecture

**Status:** Stable · **Last updated:** 2026-05-30

How the v1 negotiation ride is implemented. This is the "core" slice (decision D-026): the engine,
scenario generator, scoring, scripted house cast, baseline/heuristic agents, and a CLI — plus the
**nudge controls** (decision D-029). The HTTP server, replay viewer, and a real LLM agent are
deferred (see [`04-open-questions.md`](04-open-questions.md)).

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
| `suite.py` | `Suite` (seed + counts) and `run_suite(suite, agent, nudge=None)` — agent × every persona × every scenario; a `Nudge` restricts the roster / injects a scenario and flags the run off-record. |
| `runlog.py` | Writes a JSON run log (profile + per-match transcripts) to `runs/` — the replay viewer's input. Versioned (`schema_version`) with a top-level `off_record` flag (D-029). |
| `nudge.py` | `Nudge` spec, the persona-name registry, and `parse_scenario_spec()` (inline JSON or file). Powers the observe+nudge loop (D-029); keeps CLI/suite edits localized. |
| `cli.py` | `parkbench run` (incl. `--swap-persona`, `--inject-scenario`, `--off-record`) and `parkbench analyze`. |

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

The log is **versioned** so the server/replay slices can detect shape changes. D-029 set
`schema_version = 2` and added the `off_record` flags; **all pre-existing fields are unchanged and in
their original positions** (additions only). Fields added by D-029:

| Field | Type | Location | Meaning |
|---|---|---|---|
| `schema_version` | `int` | top level | Run-log schema version (currently `2`). Absent ⇒ treat as `1`. |
| `off_record` | `bool` | top level | Whether the whole run was nudged/off-record (default `false`). |
| `off_record` | `bool` | each entry of `matches[]` (appended last) | Per-match off-record flag (mirrors the run flag in v1). |

Existing top-level keys remain `suite`, `profile`, `matches`; existing per-match keys
(`scenario_seed`, `persona`, `agreed`, `outcome`, `efficiency`, `own_value`, `turns_used`,
`transcript`, `analysis`) are untouched. Off-record runs also get a `__off_record` directory suffix.

## Agents & personas

| Name | Kind | Behavior |
|---|---|---|
| `random` | baseline / floor | Random offers; accepts ~25% of the time. |
| `greedy` | baseline | Always demands its own best; never concedes; rarely closes. |
| `heuristic` | test (good) | Time-based concession; concedes cheap issues first (logrolling). |
| `tough` / `fair` / `cooperative` / `slippery` | house cast | One `ConcederStrategy` tuned to four dispositions; `slippery` adds RNG noise. |

## How to run

```bash
uv venv && uv pip install -e ".[dev]"      # or: python -m venv .venv && pip install -e ".[dev]"
pytest                                      # 28 tests
parkbench run --agent heuristic --seed 1    # run the suite, print a profile, write a run log
parkbench run --agent greedy --seed 1       # compare a weaker strategy
parkbench analyze --seed 1                  # inspect one scenario's optimum

# Nudge controls (D-029) — these runs are off-record and excluded from canonical scores:
parkbench run --agent heuristic --swap-persona tough            # face only the tough persona
parkbench run --agent heuristic --inject-scenario scn.json      # run a supplied scenario (or inline JSON)
parkbench run --agent heuristic --off-record                    # force off-record without nudging
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

HTTP/JSON server (external BYO agents), the static replay viewer, and a real LLM reference agent —
tracked in [`04-open-questions.md`](04-open-questions.md).
