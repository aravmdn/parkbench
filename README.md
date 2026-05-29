# Parkbench

**A modular benchmark arena for AI agents, themed as a theme park.** Each "ride" is a
self-contained, scored test of a capability, and an agent comes out with a diagnostic *skill
profile*. The goal is to become a **trusted, reproducible** place to measure agents — especially on
the things single-agent, single-task benchmarks can't reach: multi-agent negotiation, coalitions,
trust/deception, and robustness under pressure.

> **Status: pre-implementation.** The scope and the first ride are designed; there is no code yet.

## What's here

Right now this repo holds the project's documentation. **Start with [`docs/`](docs/)** —
[`docs/00-vision.md`](docs/00-vision.md) explains what Parkbench is and why, and
[`docs/01-v1-scope.md`](docs/01-v1-scope.md) defines the first build.

- [`CLAUDE.md`](CLAUDE.md) — operating instructions for AI agents working in this repo.
- [`docs/`](docs/) — vision, v1 scope, decision log, roadmap, open questions, glossary.

## v1 in one paragraph

The first ride is **multi-issue negotiation**: a bring-your-own agent negotiates integrative,
multi-issue deals against a fixed cast of house personas, and is scored by objective payoff (value
captured, measured against the game-theoretic optimum and a weak baseline) across a fixed scenario
suite. It exists to prove the hard part — that a multi-agent social interaction can be turned into a
trustworthy, reproducible score. See [`docs/01-v1-scope.md`](docs/01-v1-scope.md).

## Documentation-first

Every decision and design lives in `docs/` and is meant to stay in sync with reality. The full
rationale trail is in [`docs/02-decisions.md`](docs/02-decisions.md).
