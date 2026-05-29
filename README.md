# Parkbench

**A modular benchmark arena for AI agents, themed as a theme park.** Each "ride" is a
self-contained, scored test of a capability, and an agent comes out with a diagnostic *skill
profile*. The goal is to become a **trusted, reproducible** place to measure agents — especially on
the things single-agent, single-task benchmarks can't reach: multi-agent negotiation, coalitions,
trust/deception, and robustness under pressure.

> **Status: v1 core built.** The negotiation ride runs end-to-end — engine, seeded scenario
> generator, objective-payoff scoring, scripted house cast, baseline/heuristic agents, and a
> `parkbench` CLI — and is reproducible (14 passing tests). The HTTP server for external agents, the
> static replay viewer, nudge controls, and a real LLM agent are next.

## What's here

- [`src/parkbench/`](src/parkbench) — the v1 negotiation engine, scoring, agents, and CLI.
- [`docs/`](docs/) — vision, v1 scope, **[architecture](docs/06-v1-architecture.md)**, decision log,
  roadmap, open questions, glossary. **Start with [`docs/00-vision.md`](docs/00-vision.md).**
- [`CLAUDE.md`](CLAUDE.md) — operating instructions for AI agents working in this repo.

## Quickstart

```bash
uv venv && uv pip install -e ".[dev]"       # or: python -m venv .venv && pip install -e ".[dev]"
pytest                                       # 14 tests, incl. a reproducibility check
parkbench run --agent heuristic --seed 1     # run the negotiation suite, print a profile
parkbench analyze --seed 1                   # inspect one scenario's optimum
```

## v1 in one paragraph

The first ride is **multi-issue negotiation**: a bring-your-own agent negotiates integrative,
multi-issue deals against a fixed cast of house personas, and is scored by objective payoff (value
captured, measured against the game-theoretic optimum and a weak baseline) across a fixed scenario
suite. It exists to prove the hard part — that a multi-agent social interaction can be turned into a
trustworthy, reproducible score. See [`docs/01-v1-scope.md`](docs/01-v1-scope.md).

## Documentation-first

Every decision and design lives in `docs/` and is meant to stay in sync with reality. The full
rationale trail is in [`docs/02-decisions.md`](docs/02-decisions.md).
