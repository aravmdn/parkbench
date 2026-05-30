# Parkbench

**A modular benchmark arena for AI agents, themed as a theme park.** Each "ride" is a
self-contained, scored test of a capability, and an agent comes out with a diagnostic *skill
profile*. The goal is to become a **trusted, reproducible** place to measure agents — especially on
the things single-agent, single-task benchmarks can't reach: multi-agent negotiation, coalitions,
trust/deception, and robustness under pressure.

> **Status: v1 core + all four follow-ups built.** The negotiation ride runs end-to-end — engine,
> seeded scenario generator, objective-payoff scoring, scripted house cast (with per-persona
> reservation floors), baseline/heuristic agents, and a `parkbench` CLI — plus an **HTTP/JSON
> server** for external BYO agents, a **static replay viewer**, **nudge controls** (off-record), and
> a real **LLM reference agent** via OpenRouter. Reproducible: **57 passing tests**.

## What's here

- [`src/parkbench/`](src/parkbench) — the negotiation engine, scoring, agents (incl. the OpenRouter
  `llm` agent), nudge controls, and the HTTP/JSON server + CLI.
- [`viewer/`](viewer) — the static, dependency-free replay viewer for `run.json` logs.
- [`docs/`](docs/) — vision, v1 scope, **[architecture](docs/06-v1-architecture.md)**, decision log,
  roadmap, open questions, glossary. **Start with [`docs/00-vision.md`](docs/00-vision.md).**
- [`CLAUDE.md`](CLAUDE.md) — operating instructions for AI agents working in this repo.

## Quickstart

```bash
uv venv && uv pip install -e ".[dev]"       # or: python -m venv .venv && pip install -e ".[dev]"
pytest                                       # 57 tests, incl. a reproducibility check
parkbench run --agent heuristic --seed 1     # run the negotiation suite, print a profile
parkbench run --agent llm --seed 1           # the OpenRouter LLM agent (reads .env; see docs/06)
parkbench analyze --seed 1                   # inspect one scenario's optimum
parkbench serve --port 8080                  # host a run over HTTP for an external BYO agent
```

Replay a run in the browser: open [`viewer/index.html`](viewer/index.html) and load
[`viewer/sample-run.json`](viewer/sample-run.json) (no server needed).

## v1 in one paragraph

The first ride is **multi-issue negotiation**: a bring-your-own agent negotiates integrative,
multi-issue deals against a fixed cast of house personas, and is scored by objective payoff (value
captured, measured against the game-theoretic optimum and a weak baseline) across a fixed scenario
suite. It exists to prove the hard part — that a multi-agent social interaction can be turned into a
trustworthy, reproducible score. See [`docs/01-v1-scope.md`](docs/01-v1-scope.md).

## Documentation-first

Every decision and design lives in `docs/` and is meant to stay in sync with reality. The full
rationale trail is in [`docs/02-decisions.md`](docs/02-decisions.md).
