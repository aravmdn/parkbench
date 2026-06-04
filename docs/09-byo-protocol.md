# 09 — BYO agent protocol (HTTP/JSON)

**Status:** Living · **Last updated:** 2026-06-04

This is the wire spec a third party implements to bring their own (BYO) agent to Parkbench's
negotiation ride over HTTP/JSON. It is the documented contract for the server built in **D-027**
(implementing **D-015**); the implementation lives in `src/parkbench/server.py` (+ a reference client
in `src/parkbench/client.py`). Roadmap [#5](03-roadmap.md) is "grow the BYO ecosystem" — this doc is
the "document the protocol" half of it.

> **Scope.** v1 BYO covers the **negotiation** ride only (the multi-agent ride where a remote
> counterpart is meaningful). The solo rides (economic/coding/safety/commons) are scored from
> submitted artifacts/agents in-process, not over this wire.

## Design in one line

**The park drives the loop.** The agent is a pure HTTP **client**: it *polls* for its turn and *posts*
its move. The park runs the negotiation engine, owns the house cast, and stays in control of timing —
which is what keeps runs deterministic and reproducible (D-015). The agent needs **no inbound server**,
so any language/framework that can make outbound HTTP calls can play.

## Starting a run (the park side)

```bash
parkbench serve --seed 1 --port 8080 --agent-name my-bot
# listening on http://127.0.0.1:8080
#   GET /observation   POST /action   GET /health
```

The park binds, runs the suite in a background thread, and answers the external agent as side **A**
(the test side). `--port 0` picks an ephemeral port. (`--local-agent heuristic` drives the run
in-process over the same HTTP for a self-test.)

## Endpoints

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

## Message shapes

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

## Determinism contract

Reproducibility is the whole project's foundation, so the protocol preserves it:

- The park re-seeds **its own** side-A bridge per match and forwards that match's `seed` /
  `total_rounds` to the client via `new_match` on the first turn. A client that re-seeds its agent
  with those values reproduces a pure in-process run **byte-for-byte** (verified by the parity tests
  in `tests/test_server.py`). A seed-independent agent (e.g. the heuristic) matches regardless.
- The park is the single source of timing/turn order; the agent never advances the clock. There is no
  hidden state on the wire beyond what the observation carries.

## Security & trust

- The park **never executes the agent's code** — the agent runs on the agent's own machine and only
  exchanges JSON, so there is no server-side code-execution surface for the negotiation wire. (Untrusted
  *code* execution applies to the coding ride's harness, which is separately sandboxed — D-043/D-048;
  see [`04-open-questions.md`](04-open-questions.md).)
- The server validates and rejects malformed actions (`400`) and out-of-turn posts (`409`).
- v1 is unauthenticated and intended for `127.0.0.1` / trusted-network use. Authentication, rate
  limiting, TLS, and multi-tenant hosting are part of the remaining BYO-hardening work (roadmap #5),
  not yet implemented — do not expose `parkbench serve` to an untrusted network as-is.

## Still open (roadmap #5)

Documented here, deferred in code: auth + transport security for public hosting; a published JSON
Schema for the messages; and BYO connectors for the **solo** rides (submit-an-artifact for coding, a
move endpoint for economic/safety/commons) so the whole park — not just negotiation — is reachable by
a third party. See [`03-roadmap.md`](03-roadmap.md) #5.
