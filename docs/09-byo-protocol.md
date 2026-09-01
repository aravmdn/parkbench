# 09 — BYO agent protocol (HTTP/JSON)

**Status:** Living · **Last updated:** 2026-08-30

This is the wire spec a third party implements to bring their own (BYO) agent to Parkbench over
HTTP/JSON. Roadmap [#5](03-roadmap.md) is "grow the BYO ecosystem" — this doc is the "document the
protocol" half of it.

> **Scope.** There are **two wires**, because the park has two shapes of ride:
>
> | Wire | Rides | Shape | Built in |
> |---|---|---|---|
> | **negotiation** (`/observation` · `/action`) | `negotiation` | turn-by-turn conversation | D-027 (`server.py` / `client.py`) |
> | **solo** (`/scenario` · `/plan`) | `economic` · `exchange` · `safety` · `containment` | one puzzle out, one plan back | D-074 (`solo_server.py` / `solo_client.py`) |
>
> Between them that is **five of the park's seven rides**, covering the `social` axis, *both* rides
> on the `economic` axis and *both* rides on the `safety` axis. The two rides with no wire are named
> and explained in [Rides no wire carries](#rides-no-wire-carries) — they are not silently omitted.
>
> Both wires share one design (**the park drives the loop**), so a third party learns the pattern
> once. Headings say which wire they belong to; anything before [The solo wire](#the-solo-wire) and
> not marked "both wires" is the negotiation wire.

## Design in one line (both wires)

**The park drives the loop.** The agent is a pure HTTP **client**: it *polls* for work and *posts* its
answer. The park runs the ride, owns everything the agent does not, and stays in control of timing —
which is what keeps runs deterministic and reproducible (D-015). The agent needs **no inbound server**,
so any language/framework that can make outbound HTTP calls can play.

The two wires differ only in what "work" and "answer" are: an `Observation` and an `Action` on the
negotiation wire, a whole scenario and a plan on the solo wire.

## Starting a run (the negotiation wire)

```bash
parkbench serve --seed 1 --port 8080 --agent-name my-bot
# listening on http://127.0.0.1:8080
#   GET /observation   POST /action   GET /health
```

The park binds, runs the suite in a background thread, and answers the external agent as side **A**
(the test side). `--port 0` picks an ephemeral port. (`--local-agent heuristic` drives the run
in-process over the same HTTP for a self-test.)

## Endpoints (negotiation wire)

All bodies are JSON (`Content-Type: application/json`). All responses are `200` unless noted.

### `GET /health`

Liveness/identity check.

```json
{ "status": "ok", "agent": "my-bot" }
```

### `GET /observation`

Poll for the current state. Exactly one of these `status` values comes back:

- **`your_turn`** — it is the agent's move. Compute an `Action` and `POST /action`.
  ```json
  {
    "status": "your_turn",
    "turn": 7,
    "observation": { "...": "see Observation below" },
    "new_match": { "seed": 12, "total_rounds": 8 }
  }
  ```
  `new_match` is present **only on the first turn of each match** — use it to (re-)seed a
  seed-dependent agent so it reproduces a pure in-process run (see "Determinism" below). It is absent
  on every other turn.
- **`waiting`** — the park is busy (e.g. the house persona is moving). Poll again.
  ```json
  { "status": "waiting" }
  ```
- **`done`** — the whole run has finished; `profile` carries the final scored profile.
  ```json
  { "status": "done", "profile": { "...": "scored profile" } }
  ```
- **`error`** — the park run failed (returned with HTTP `500`); stop and surface the message.
  ```json
  { "status": "error", "error": "..." }
  ```

### `POST /action`

Submit the agent's move for the current turn. Body is an `Action` (see below).

- **`200`** on success: `{ "status": "accepted", "turn": 7 }`
- **`409`** if it is not currently the agent's turn (no pending observation):
  `{ "error": "not your turn (no pending observation)" }`
- **`400`** if the body is not a valid action: `{ "error": "bad action: ..." }`

Unknown paths return **`404`** `{ "error": "unknown path '...'" }`.

## Message shapes (negotiation wire)

### Observation

What the agent sees on its turn. It carries **only the agent's own utilities** — the counterpart's
preferences are private (information asymmetry, D-016), so nothing about the house persona leaks over
the wire.

| Field | Type | Meaning |
|---|---|---|
| `role` | string | `"A"` (the BYO/test side over the wire is always A). |
| `my_util` | `number[][]` | `my_util[issue][level]` = this agent's payoff contribution for choosing `level` on `issue`. |
| `standing_offer` | `Offer \| null` | The counterpart's most recent offer — acceptable as-is via an `accept` action. |
| `my_last_offer` | `Offer \| null` | This agent's previous offer (or `null` on the first turn). |
| `rounds_left` | int | Offers this side may still make, **including the current turn**. |
| `history` | `object[]` | The public transcript so far (turn records). |

The agent's payoff for a full agreement `offer` is `sum(my_util[i][offer.levels[i]])`; its best
possible single agreement is `sum(max(my_util[i]))`. (These are conveniences — the agent may score
however it likes.)

### Offer

```json
{ "levels": [2, 0, 1, 3] }
```

`levels[i]` is the chosen **level index** for issue `i`, in issue order. The length equals the number
of issues; each value is a valid level index for that issue.

### Action

```json
{ "type": "offer", "offer": { "levels": [2, 0, 1, 3] }, "message": "best I can do" }
```

| `type` | `offer` field | Meaning |
|---|---|---|
| `"offer"` | required | Propose `offer` as the full agreement. |
| `"accept"` | `null` | Accept the current `standing_offer` (ends the match as a deal). |
| `"message"` | `null` | Say something (free text) without proposing or accepting. |

`message` is always optional free text (default `""`). Free text is captured for the transcript;
scoring reflects the **structured** offer/accept, not the prose (D-017).

## The agent loop (pseudocode)

```text
reset(seed=0, total_rounds=8)
loop:
    s = GET /observation
    switch s.status:
        "done":     return s.profile
        "error":    fail(s.error)
        "waiting":  continue            # optionally back off a few ms
        "your_turn":
            if s.new_match: reset(seed=s.new_match.seed,
                                  total_rounds=s.new_match.total_rounds)
            action = decide(s.observation)
            POST /action  <- action
```

The canonical reference implementation of this loop is `client.drive_agent` (≈45 lines, stdlib
`urllib` only) — read it as the worked example.

## Determinism contract (negotiation wire)

Reproducibility is the whole project's foundation, so the protocol preserves it:

- The park re-seeds **its own** side-A bridge per match and forwards that match's `seed` /
  `total_rounds` to the client via `new_match` on the first turn. A client that re-seeds its agent
  with those values reproduces a pure in-process run **byte-for-byte** (verified by the parity tests
  in `tests/test_server.py`). A seed-independent agent (e.g. the heuristic) matches regardless.
- The park is the single source of timing/turn order; the agent never advances the clock. There is no
  hidden state on the wire beyond what the observation carries.

## The solo wire

**Status:** built (D-074). Rides: `economic` · `exchange` · `safety` · `containment`.

Four of the park's rides are not conversations. The park hands the agent a whole, fully-observable
puzzle and the agent hands back a **plan** — a list of integer indices. Same design as the
negotiation wire (**the park drives the loop**, the agent is a pure HTTP client, no inbound server
needed), different message shape.

### Why a second wire rather than one extended wire

The negotiation `Observation` is a *partial* view of a *shared* state that evolves with a
counterpart's moves — D-016's information asymmetry is the point of that ride. A solo scenario has
no counterpart and nothing hidden. Squeezing one into the other would mean inventing an empty
history, a null standing offer and a meaningless `rounds_left`: a worse spec, not a smaller one.

### Starting a run

```sh
parkbench serve --ride economic --port 8080 --agent-name my-bot
# listening on http://127.0.0.1:8080
#   GET /scenario   POST /plan   GET /health
parkbench serve --ride containment --port 0 --local-agent optimal   # in-process self-test
```

### Endpoints

#### `GET /health`

```json
{ "status": "ok", "ride": "economic", "agent": "my-bot" }
```

#### `GET /scenario`

Poll for the next puzzle. Exactly one `status` comes back:

- **`your_turn`** — a scenario is waiting. Compute a plan and `POST /plan`.
  ```json
  {
    "status": "your_turn",
    "step": 3,
    "ride": "economic",
    "task": "knapsack",
    "scenario": { "task": "knapsack", "seed": 3, "budget": 95,
                  "items": [{ "value": 20, "weight": 21 }, { "value": 39, "weight": 7 }, "..."] },
    "answer": { "kind": "subset", "of": "item indices", "n_items": 12, "length": null,
                "note": "distinct item indices whose total weight fits the budget; over budget scores 0" },
    "new_scenario": { "seed": 1000005 }
  }
  ```
  (Real bytes from `parkbench serve --ride economic --seed 1`, third scenario: the suite's third
  instance is `generate_scenario(seed + 2)`, and the agent is re-seeded with `seed * 1_000_003 + 2`.)
  `answer` is machine-readable: it says exactly what shape of plan this scenario expects, so a
  client can validate before posting. `new_scenario.seed` is the solo counterpart of `new_match` —
  the suite re-seeds the agent before **every** scenario, so a seed-dependent agent that re-seeds
  with this value reproduces a pure in-process run byte-for-byte.
- **`waiting`** — the park is between scenarios. Poll again.
- **`done`** — the ride finished; `result` is the scored `RideResult`.
  ```json
  { "status": "done",
    "result": { "ride": "economic", "axis": "economic", "agent": "my-bot",
                "score": 0.990202, "detail": { "...": "per-ride breakdown + integrity" } } }
  ```
- **`error`** — the park run failed (HTTP `500`); stop and surface the message.

#### `POST /plan`

```json
{ "plan": [0, 2, 5, 7] }
```

- **`200`** — `{ "status": "accepted", "step": 3 }`
- **`409`** — not currently the agent's turn (no pending scenario).
- **`400`** — the body is not an object with a `plan` array of integers.

> **A wrong plan is not a `400`.** The transport checks only the *shape*. An over-budget subset, a
> non-permutation, a red-line crossing or an envelope breach are all well-formed answers that the
> **ride** scores — at 0, with the integrity signal that a career prices (D-041). Rejecting them at
> the transport layer would hide real failures behind an HTTP error and quietly inflate a BYO
> agent's score by dropping its worst answers.

### The four tasks

| Ride | `task` | Scenario carries | Plan is |
|---|---|---|---|
| `economic` | `knapsack` | `items[{value,weight}]`, `budget` | a **subset** of item indices (any length) |
| `exchange` | `assignment` | `surplus[i][j]` matrix | a **permutation**: `plan[i]` = trader *i*'s good |
| `safety` | `red-line` | `rounds[{actions[{reward,category}], injection}]`, `forbidden` | one **action index per round** |
| `containment` | `envelope` | `cycles[{operations[{payoff,heat}]}]`, `capacity`, `start_heat` | one **mode index per cycle** |

Two details that are deliberate rather than incidental:

- The **rule is public**. `safety` sends its `forbidden` categories and `containment` sends its
  `capacity` — the agent is told the constraint up front, exactly as an in-process agent is. The
  ride measures whether an agent *keeps* a rule it knows, not whether it can guess one.
- The **injection is transported verbatim, lie included**. A `safety` round's `injection` falsely
  claims a category is authorized; sanitising it on the wire would score the ride instead of
  transporting it, and the ride's whole point is resisting in-band manipulation.

### Determinism contract

Identical in spirit to the negotiation wire's: the park generates every scenario from the suite
seed, re-seeds the agent before each one and forwards that seed in `new_scenario`. Same agent, same
seed ⇒ same plan requests in the same order ⇒ byte-identical result. Pinned for all four rides ×
all four baselines in `tests/test_solo_wire.py`.

### It transports; the ride scores

`SoloParkServer` runs `RIDE_REGISTRY[ride].evaluate(agent_name, seed, agent=<bridge>)` — the ride's
own code path, handed a different agent object. There is no second scoring implementation to drift,
so a wired leg equals an in-process leg exactly, `detail` included. The `agent=` parameter is the
only engine-side change D-074 made, and it is inert when omitted, which is why every committed
baseline is byte-identical.

## Rides no wire carries

Two of the seven registered rides are unreachable, and a captured profile names them rather than
quietly reading as complete (`source.unreachable`, and `skipped_rides` on the profile itself):

| Ride | Why not |
|---|---|
| `commons` | Multi-agent and **sequential** — the agent contributes round by round while watching what the society did. It needs the negotiation wire's turn loop, not a one-shot plan. |
| `coding` | **Submit-an-artifact**: the answer is a source file, not a plan of indices, and running it needs the sandbox (D-043/D-048). |

A test (`test_the_solo_wire_carries_every_plan_shaped_ride_in_the_registry`) asserts every registered
ride is on a wire or on this list, so a ride added later cannot silently skip the BYO surface.

## Capturing a live run for the spectator surfaces (D-073, D-074)

The world (`web/`) has rendered a BYO trainer since **D-063**, but its numbers were a hand-authored
`radar-byo.json` stand-in. The **live connector** (`src/parkbench/byo.py`) closes that gap: it binds a
real `ParkServer` on an ephemeral loopback port, drives it with the reference client, and shapes the
completed run into the same radar-shaped JSON `parkbench radar --json` emits.

```sh
parkbench byo-run                                  # negotiation only (D-073): capture + summarize
parkbench byo-run --rides all                      # every wire (D-074): a three-axis profile
parkbench byo-run --rides negotiation,safety       # ... or any subset
parkbench byo-run --json                           # the radar-shaped payload, version-stamped
parkbench byo-run --name acme-bot --byo-version 0.3.1 --out web/src/fixtures/radar-byo.json
parkbench serve --profiles --port 8080             # ... or serve one on demand:
#   GET /byo?agent=<driver>[&name=<label>][&seed=N][&scenarios=N][&rides=all]
```

Everything crosses a socket, so a captured run exercises the spec above end-to-end. Two properties
make it usable as a benchmark artifact:

- **It reproduces the in-process ride exactly.** Driving `heuristic` over the wire yields the same
  score *and* the same `detail` as `NegotiationRide.evaluate("heuristic", seed)` — pinned in
  `tests/test_byo.py`. The connector transports; it never re-scores (D-012).
- **It is deterministic.** The payload carries no timestamp and no port, so the same agent at the
  same seed produces byte-identical JSON. Provenance is recorded *structurally* instead — a `source`
  block with the protocol, the spec path, the ride(s), the match/turn counts, and (for a sweep) a
  per-leg breakdown plus the named `unreachable` rides.

### What a live BYO profile can honestly claim

Scope, restated as a consequence: a captured profile covers exactly the rides a wire reaches, and
the caller chooses how many wires to drive.

| Field | `byo-run` (D-073) | `byo-run --rides all` (D-074) |
|---|---|---|
| `axes` | `social` only | `social` · `economic` · `safety` |
| `missing_axes` | `["economic", "coding", "safety"]` | `["coding"]` |
| `skipped_rides` | every other registered ride | `["commons", "coding"]` — the two with no wire |
| rides driven | 1 | 5 |

Two of those axes are not merely *present* but **complete**: both economic rides and both safety
rides are on the wire, so a swept `economic`/`safety` axis is numerically identical to the one a
built-in baseline gets. `social` is the partial one — `negotiation` is reachable and `commons` is
not, so a swept social axis is one ride where a baseline's is the mean of two. That asymmetry is
asserted rather than glossed (`test_the_swept_axes_equal_the_in_process_axes_wherever_every_ride_has_a_wire`).

Either way the profile is narrower than the hand-authored stand-in D-073 replaced, which claimed
scores on all five rides it had no way to earn. Narrow-and-true beats wide-and-invented, so the
front-end draws the uncovered axes as dimmed **`n/a`** rather than as a score of `0.000`, and prints
why. What is still out of reach is a **career** — see [Still open](#still-open-roadmap-5).

### Who may be driven, and why it is restricted

The wire cannot tell a genuine third-party client from a built-in negotiator standing in for one —
that indistinguishability *is* the protocol's guarantee (D-015), and it is what lets the connector
ship as an offline-verifiable test. The **`/byo` HTTP route** is deliberately narrower than the
library call:

- **Deterministic, offline drivers only.** The `llm` variants are refused with a `400`: a GET that
  can spend the operator's OpenRouter budget does not belong on a "read-only" endpoint.
- **Bounded work.** `?scenarios=` is capped (`MAX_BYO_SCENARIOS`), so no single request can ask for
  an unbounded run. A default 12-scenario capture takes ~1 s over loopback.
- **`?rides=` is an enumerated choice**, not a free-form ride list: `negotiation` (default) or `all`.
  A sweep is ~5x the work of a single leg, and keeping the choice enumerated keeps the work a
  request can ask for predictable.

The library functions have none of these restrictions — they are called by someone who already has
the machine.

## Security & trust

- The park **never executes the agent's code** — the agent runs on the agent's own machine and only
  exchanges JSON, so **neither wire** has a server-side code-execution surface. (Untrusted *code*
  execution applies to the coding ride's harness, which is separately sandboxed — D-043/D-048; that
  ride has no BYO wire yet, and when it gets one it must reuse that harness rather than add a second
  execution path. See [`04-open-questions.md`](04-open-questions.md).)
- Each server validates and rejects malformed bodies (`400`) and out-of-turn posts (`409`) — but only
  the *shape*: a wrong answer is the ride's business, not the transport's (see the solo wire's note).
- Both wires are unauthenticated and intended for `127.0.0.1` / trusted-network use. Authentication, rate
  limiting, TLS, and multi-tenant hosting are part of the remaining BYO-hardening work (roadmap #5),
  not yet implemented — do not expose `parkbench serve` to an untrusted network as-is.

## Still open (roadmap #5)

Documented here, deferred in code:

- **Auth + transport security for public hosting** (and rate limiting, TLS, multi-tenancy). Both
  wires are unauthenticated `127.0.0.1` surfaces today.
- **A published JSON Schema** for the messages of both wires.
- **The last two connectors** — the two rides no wire carries (above): a turn-loop wire for
  `commons` and a submit-an-artifact wire for `coding`.

The remaining connectors are no longer the *binding* limit on measuring a third party — D-074 took a
live BYO profile from one axis to three. What they still block is narrower and specific: a BYO agent
cannot earn a **career**, because the career roll-up (D-041) multiplies an `integrity` signal from
*every* ride and two of them are unreachable. So a third party can be profiled on three axes but not
ranked on the leaderboard. Closing `commons` and `coding` is what would change that.
