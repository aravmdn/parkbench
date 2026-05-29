# 01 — v1 Scope

**Status:** Stable · **Last updated:** 2026-05-29

## Scope discipline

The full vision is four skills × both ride formats. That is the **destination**, not v1. v1 exists
to **prove the hard part**, and the hard part is *reproducible scoring of a social skill* — **not**
spectacle. Everything below is **one ride**.

## The flagship ride: multi-issue negotiation

- A bring-your-own (BYO) **test agent** negotiates deals with a **fixed house cast** of
  counterparties across several issues / resources.
- **Independent ride** — no cross-ride coupling, no persistent "career" in v1.
- **Thin theme** — minimal skin; mechanics come first.

## Scoring: objective payoff vs. baselines

- **Score = value captured / goal achieved, normalized against reference agents.**
- Rigorous, reproducible, hard to game.
- **No** judge-LLM and **no** peer ratings in v1 — they add bias/gameability and aren't needed to
  prove the scoring backbone. (They are candidates for *later* qualitative axes — see roadmap.)

## Why it's reproducible by construction

Fixed house cast + objective payoff + a fixed scenario set ⇒ stable scores across runs. This is the
direct application of the "house cast = scoring infrastructure" insight from
[`00-vision.md`](00-vision.md).

## What v1 proves

That a multi-agent social interaction can be turned into a **trustworthy, reproducible, low-variance
score** for a BYO agent. If that holds, the rest of the park is "more rides."

## Success criteria for v1

- [ ] The same agent, scored repeatedly on the same scenarios, yields **stable, low-variance** scores.
- [ ] Stronger and weaker reference agents are **clearly separated** by the score (it discriminates).
- [ ] A third-party agent can connect over the published protocol and be scored **without bespoke glue**.
- [ ] A human can **watch a negotiation replay** and **nudge** (inject a scenario / coach) and see
      the effect — the observe+nudge loop works end-to-end on one ride.

## Explicitly OUT of scope for v1

- The other three skill axes (Economic / Coding / Safety) — beyond, at most, a placeholder on the radar.
- Cross-ride "career" / persistent reputation & resources.
- Social-deduction and other ride formats.
- Any monetization, accounts, or billing.
- Heavy theming, names, lore, or a polished spectator UI.

## v1 ride design (decided 2026-05-29)

Locked via decisions D-015–D-021 (see [`02-decisions.md`](02-decisions.md)):

- **Connection (D-015):** BYO agents connect over a plain **HTTP/JSON** API; the **park orchestrates**
  the loop — it sends a JSON observation on the agent's turn and receives a JSON action. (An MCP
  wrapper is a later convenience, not v1.)
- **Negotiation structure (D-016):** **integrative**, **3–5 issues**, **asymmetric private
  preferences** (each side knows only its own weights). Rewards discovering value-creating trades.
- **Interaction (D-017):** **turn-based**, **capped rounds / deadline**; each turn allows a
  **free-text message** plus a **structured offer/accept** action.
- **House cast (D-018):** **bilateral** (one counterpart per run) from a **roster of 3–4 fixed
  personas** (tough / fair / cooperative / slippery), **temperature 0 or fixed seed**, frozen prompts.
  The test agent faces each persona.
- **Scoring (D-019):** anchor to the **game-theoretic optimum** (Pareto / Nash) as ceiling and a
  **weak floor** agent; report **joint value captured** and **own share** separately.
- **A "score" (D-020):** mean over a **fixed suite of ~10–20 scenarios**, with reported
  **variance / CI** (the variance is the evidence for the reproducibility claim).

### Observe + nudge for v1 (D-021)
Structured run logs + a simple replay viewer (transcript + running score). Nudge = inject a scenario
or swap the counterpart persona; nudged runs are flagged **off-record** and excluded from canonical
profiles.

### Still deferred
Per-scenario preference generation, the exact persona prompts, the round-cap value, the log/replay
schema, radar roll-up across rides, anti-gaming, and agent identity/versioning — see
[`04-open-questions.md`](04-open-questions.md).
