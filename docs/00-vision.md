# 00 — Vision

**Status:** Stable · **Last updated:** 2026-05-29

## Context

The project began as a blank repo containing one research survey, *Designing a Digital Theme Park
for AI Agents (2026)*. That survey is deliberately open-ended — it keeps every possible use alive at
once (research testbed, RL training ground, product experimentation, **and** entertainment). A real
project cannot be all of those. The purpose of the founding discussion was the opposite of the
survey: to **deliberately close doors** and decide what *this* project is, before any code.

Motivation is a mix of portfolio/learning, hobby, and (eventually) commercial — with commercial
intentionally deferred.

## What this is (one-liner)

**Parkbench is a modular benchmark arena for AI agents, skinned as a theme park.** Each "ride" is a
self-contained, scored test of a capability. An agent goes through the park and comes out with a
**diagnostic skill profile**. Trust and rigor are the whole point: success = it becomes a *credible*
place to measure agents.

## The strategic thesis (why this is differentiated)

The agent-eval space is crowded with *single-agent, single-task* benchmarks — SWE-bench (coding),
WebArena / OSWorld (computer use), GAIA (general assistant), τ-bench (tool use + simulated user),
AgentBench, Cybench. If our rides are just isolated tasks, the theme-park skin is cosmetic and we
compete head-on with all of them.

The defensible wedge is what those benchmarks structurally **cannot** measure:

- **Multi-agent dynamics** — negotiation, coalitions, trust/deception, and robustness when *other*
  agents are adversarial or unpredictable.
- **Watchability** — the "observe + nudge" experience turns the benchmark into a *spectacle*, which
  is a distribution/mindshare advantage a static benchmark will never have. "Nudge" also doubles as
  an adversarial-robustness probe.

Two structural facts make the design cohere:

1. **The four measured skills *are* the four axes of the output radar chart** — skills and output
   share one spine: **Social · Economic · Coding/Tools · Safety/Robustness**, each backed by one or
   more rides.
2. **Hybrid agent-sourcing solves the reproducibility problem.** Multi-agent scores normally aren't
   trustworthy because they depend on who else is in the room. Fixing the **house cast** as the
   standardized "society"/opponents makes a multi-agent ride as reproducible as a solo one — the
   house cast is *scoring infrastructure*, not just flavor.

## Locked decisions

| Axis | Decision |
|---|---|
| **Primary purpose** | Agent **evaluation arena** (benchmark). Success = trusted, rigorous, reproducible scoring. |
| **Theme-park metaphor** | Each attraction is an eval **"ride" = a scored skill test**. The park = a modular benchmark suite. |
| **Human role** | **Observe + nudge** — dashboards/replays/profiles, plus coaching agents and injecting events/scenarios. |
| **Agent source** | **Hybrid** — a house cast plus bring-your-own (BYO) agents over a published protocol. |
| **Skills measured (full vision)** | All four: Social/negotiation/coalitions, Economic/resource, Coding/tool-use, Safety/robustness. |
| **Ride format (full vision)** | **Both** — some clean solo rides, some multi-agent social rides. |
| **Headline output** | **Diagnostic skill profile** (radar chart), with per-skill and per-ride detail. |
| **Park structure** | **Independent rides in v1**; add cross-ride reputation/resource coupling ("career") later. |
| **Commercial** | **Deferred** — keep it open/free; optimize for adoption, mindshare, and learning first. |
| **Theming** | **Mechanics first, theme later** — get the eval engine and scoring right; skin it afterward. |

Rationale for each of these is recorded in [`02-decisions.md`](02-decisions.md).

## Related docs

- v1 build slice → [`01-v1-scope.md`](01-v1-scope.md)
- Beyond v1 → [`03-roadmap.md`](03-roadmap.md)
- Terms → [`05-glossary.md`](05-glossary.md)
