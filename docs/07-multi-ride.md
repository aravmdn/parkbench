# 07 — Multi-ride & the radar profile

**Status:** Living · **Last updated:** 2026-05-31

The post-v1 phase (decision **D-034**). v1 proved one ride can be scored reproducibly; this phase
delivers the project's headline output — the **diagnostic radar profile across skill axes** (D-007)
— which needs **≥2 rides on different axes**. See the roadmap ([`03-roadmap.md`](03-roadmap.md) #1).

## The ride abstraction (D-035)

A *ride* is a self-contained, scored capability test (D-002) that stays independent of the others
(D-008). The contract (`src/parkbench/axis.py`, `src/parkbench/rides.py`):

- **`Axis`** — one of the four skill families (D-005): `social` · `economic` · `coding` · `safety`.
- **`RideResult{ride, axis, agent, score, detail}`** — `score` is the ride's headline metric
  **normalized to `[0, 1]`** (1 = optimal), so dissimilar rides roll up onto one radar; `detail`
  holds the ride-specific breakdown.
- **`Ride`** protocol — `name`, `axis`, and `evaluate(agent_name, seed) -> RideResult`.
- **`RIDE_REGISTRY`** — the rides available for roll-up. New rides register here.

The negotiation ride (D-010) is wrapped as `NegotiationRide` (axis `social`); its normalized score is
mean efficiency. This wrapper is **additive** — the original `parkbench run` path is unchanged.

Each ride defines its own agent interface and ships its own baseline agents; the radar aggregates
whatever ride results exist for an agent.

## Economic ride (D-036)

The second ride and the first on the **economic** axis (D-005) — a **solo, deterministic 0/1
knapsack**. It is the clean solo contrast (D-006) to the multi-agent negotiation ride, and gives the
radar (D-037) its second axis. Lives in `src/parkbench/economic/`.

- **Scenario** (`scenario.py`): `generate_scenario(seed)` builds `N` items, each with an integer
  `value` and `weight`, plus an integer budget `B`. Defaults: `N=12`, budget ≈ 45% of total weight —
  the regime where value/weight greedy can miss the optimum. Same seed ⇒ byte-identical instance.
- **Optimum + scoring**: `solve_optimum` is an exact `O(N·B)` DP (cross-checked against brute force
  in tests). The score is `achieved_value / optimal_value ∈ [0, 1]`; an **infeasible** allocation
  (over budget, out-of-range, or duplicate indices) clamps to **0**. `optimal` play scores 1.0 by
  construction; `random` is the floor for context (same objective-payoff-vs-baselines backbone as
  D-011/D-019).
- **Agent interface** (its own, per D-035): an `EconomicAgent.choose(scenario) -> item indices`. The
  four baselines reuse the **negotiation ride's names** so the radar can profile a shared agent name
  across both axes: `random` (feasible floor), `greedy` (value/weight ratio), `heuristic`
  (greedy + a local-swap improvement pass), `optimal` (the DP ceiling).
- **Suite** (`suite.py`): a fixed set of ~12 seeded instances; reports mean ± 95% CI reusing
  `scoring.Stat`, so variance is reported the same way across rides.
- **Ride + registry**: `EconomicRide` (`name="economic"`, `axis="economic"`) implements
  `evaluate(agent_name, seed) -> RideResult` (normalized `score` = mean achieved/optimal; `detail`
  holds the CI, scenario count, and feasible rate). Registered as `"economic"` in `RIDE_REGISTRY`.
- **CLI**: `parkbench economic --agent <random|greedy|heuristic|optimal> --seed 1` (additive; the
  existing subcommands are untouched).
- **Results** (seed 1, 12 scenarios): `optimal` 1.000 ≥ `heuristic` 0.990 ≥ `greedy` 0.989 >
  `random` 0.659, all 100% feasible. Fully reproducible (verified across separate processes).
  Stdlib-only (D-023). +12 tests in `tests/test_economic.py` (suite total 60 → 72).

## Coding ride (D-039)

The **third** ride and the first on the **coding** axis (D-005) — a **solo, deterministic
code-generation** test that takes the radar (D-037) from two axes to three. Like the economic ride
it is the clean solo contrast (D-006) to the multi-agent negotiation ride. Lives in
`src/parkbench/coding/`.

- **Tasks** (`tasks.py`): a fixed curated `TASK_SUITE` of 9 small, self-contained problems across
  three `Difficulty` tiers (3 easy / 3 medium / 3 hard — e.g. `add`, `fib`, `is_prime`,
  `collatz_steps`, `run_length_encode`). Each `CodingTask` ships an `entry_point` name, a prompt, a
  **reference** solution (source), and a seeded `gen_inputs(rng)` input generator.
- **Harness** (`harness.py`): `grade(task, source, seed, n_tests)` compiles the candidate's source
  in an isolated namespace, generates `n_tests` inputs from the seed, computes each expected output
  by running the **reference as the oracle**, and returns the pass count. Source that fails to
  compile, lacks the entry point, raises, or returns a wrong value (strict value **and** type match)
  simply **fails** the affected tests — it never crashes the ride.
- **Two anti-gaming properties (D-039):** *(a)* the reference is the oracle, so expected answers are
  never hand-listed and can't drift; *(b)* hidden-test inputs are **seed-randomized**, so an agent
  can't pass by memorizing input→output pairs — it must implement real logic, while a correct
  solution still scores 1.0 for *any* seed. This is the ride's down-payment on the open anti-gaming
  question ([`04-open-questions.md`](04-open-questions.md)).
- **Scoring**: per-task `score = tests_passed / n_tests ∈ [0, 1]`; a *score* over the ride is the
  **mean per-task pass rate** with a 95% CI (reusing `scoring.Stat`, exactly as the other rides). The
  same objective-payoff-vs-baselines backbone as D-011/D-019/D-036.
- **Agent interface** (its own, per D-035): a `CodingAgent.solve(task) -> source str`. The four
  baselines reuse the **shared roster names** so the radar can profile one agent across axes; they
  model **capability tiers**: `random` (stub returning `None`; the floor), `greedy` (solves EASY),
  `heuristic` (solves EASY+MEDIUM), `optimal` (solves all; the 1.0 ceiling). The harness grades a
  real code-writing agent (an LLM/BYO agent that emits source) by the *exact same machinery*.
- **Ride + registry**: `CodingRide` (`name="coding"`, `axis="coding"`) implements
  `evaluate(agent_name, seed) -> RideResult` (normalized `score` = mean pass rate; `detail` holds
  the CI, task count, compile rate, and per-difficulty breakdown). Registered as `"coding"` in
  `RIDE_REGISTRY`.
- **CLI**: `parkbench coding --agent <random|greedy|heuristic|optimal> --seed 1 [--tests N]`. The
  `parkbench radar` subcommand's `--agent` choices were widened to the **union** of all ride rosters
  so any scorable agent (e.g. `optimal`, absent from the social ride) is reachable.
- **Results** (seed 1, 9 tasks × 8 tests): `optimal` 1.000 > `heuristic` 0.667 > `greedy` 0.333 >
  `random` 0.000, all 100% compile; the per-tier breakdown tracks capability exactly. Fully
  reproducible (same seed ⇒ identical hidden tests ⇒ identical scores). Stdlib-only (D-023). +16
  tests in `tests/test_coding.py` (suite total 95 → 111).

**Known limitation:** the harness does not sandbox or time-bound arbitrary code (it assumes
cooperative candidates — the in-repo baselines are). Subprocess isolation + wall-clock timeouts for
untrusted BYO code is folded into the anti-gaming / BYO-protocol hardening work
([`04-open-questions.md`](04-open-questions.md)).

## Radar roll-up (D-037)

The headline output (D-007). `src/parkbench/radar.py` turns the independent rides into one
diagnostic profile:

- **`build_radar(agent_name, seed=1, rides=None)`** iterates the rides (default `RIDE_REGISTRY`;
  `rides=` is injectable for testing — accepts a registry-like mapping or any iterable of `Ride`s),
  calls each `ride.evaluate(agent_name, seed)`, and aggregates the normalized `[0, 1]`
  `RideResult.score` **per axis (D-005) by simple mean** where several rides share an axis.
- **`RadarProfile{agent, seed, axis_scores, results, skipped}`** (frozen) is the result.
  `axis_scores` holds only the **covered** axes; an axis with no ride is **absent** and shown as
  `n/a` (a coverage gap, not a 0). `covered_axes` / `missing_axes` partition the four axes in
  canonical order.
- **Graceful skip:** a ride that can't score the agent — its roster has no entry, so `evaluate`
  raises `KeyError`/`ValueError` (D-035: each ride owns its roster) — is skipped and named in
  `skipped`, so a partially-covered agent never crashes the roll-up.
- **Rendering:** `to_dict()` gives a JSON view (stable key order); `render_radar()` draws a compact
  per-axis ASCII bar chart — **stdlib only, no plotting dependency** (D-023).
- **CLI:** `parkbench radar --agent <name> --seed 1 [--json]`.

Deterministic: rides are visited in registry/iteration order and a fixed `seed` yields identical
output. **Three** of the four axes now populate — **social** (`NegotiationRide`), **economic**
(`EconomicRide`, D-036), and **coding** (`CodingRide`, D-039); only **safety** still shows `n/a`
until a ride lands on it (roadmap #2). Rationale and rejected alternatives: **D-037** in
[`02-decisions.md`](02-decisions.md).

## Agent identity & versioning (D-038)

So results stay **attributable and reproducible over time**, every agent now has a stable identity
(`src/parkbench/agents/base.py`):

- **`Agent.identity() -> AgentIdentity{name, version, config_hash}`** — `name` is the agent's name;
  `version` defaults to the package version (`parkbench.__version__`, falling back to `"0"`);
  `config_hash` is a short (12 hex chars) **deterministic** SHA-256 of the agent's *defining* config.
- **`Agent.config() -> dict`** — the new hook each agent overrides to declare the params that
  distinguish its behaviour (default `{}`). `ConcederStrategy` returns `{start, end, noise}`;
  `LLMAgent` returns `{model}`. The per-match RNG seed is state, not config (excluded); the API key
  is a secret (never hashed).
- **Deterministic by construction:** the hash is taken over a canonical, key-sorted JSON encoding,
  so the *same agent + same code ⇒ the same identity* across instances and processes — no memory
  addresses, no object ids.
- **Backward compatible:** `config()`/`identity()` ship with sensible defaults, so every existing
  agent constructs and runs unchanged.

The identity is **stamped into the run log** as a top-level `agent` block `{name, version,
config_hash}`; the run-log `schema_version` bumps **2 → 3** (additive — see the schema notes in
[`06-v1-architecture.md`](06-v1-architecture.md)). `write_run` gained an optional `agent=` param;
when omitted the block is still emitted, derived from the profile's agent name (version `"0"`), so
older call sites keep working. This is the foundation a future leaderboard / cross-run comparison
keys on.

## Still open

Anti-gaming / reward-hacking safeguards across rides remain an open question
([`04-open-questions.md`](04-open-questions.md)). The coding ride's **seed-randomized hidden tests**
(D-039) are a first concrete safeguard against answer-memorization, and its harness flags the broader
need for **sandboxing/time-bounding untrusted code** — both feed that thread.

A **safety/robustness** ride is the remaining axis needed to complete the four-axis radar
(roadmap #2).
