# 03 — Roadmap

**Status:** Living · **Last updated:** 2026-05-31

Directional only — sequence and detail will firm up as v1 is built and learned from. v1 itself is in
[`01-v1-scope.md`](01-v1-scope.md).

## After v1 (rough order)

1. **Second ride → validate the radar with ≥2 axes.** Likely an **Economic/resource** ride — the
   closest sibling to negotiation, reusing the objective-payoff scoring. Proves the diagnostic
   profile concept with more than one data point. _(In progress, 2026-05-30: the ride abstraction
   landed (D-035); economic ride (D-036) + radar roll-up (D-037) underway.)_
2. **Fill out the four axes.** _(In progress, 2026-05-31: the **Coding/tool-use** ride landed
   (D-039) — a clean *solo* code-generation ride, hidden-test scored, taking the radar to **three**
   axes.)_ Remaining: a **Safety/robustness** ride (leans on the "nudge" mechanic as an adversarial
   probe) to complete the fourth axis.
3. **Introduce cross-ride "career."** Persistent reputation/resources across rides so choices
   compound — only once per-ride scoring is trusted (reverses part of D-008 deliberately; log it).
4. **Theming + spectator product.** Apply the creative skin; build a watchable replay/leaderboard
   experience for mindshare.
5. **Grow the BYO ecosystem.** A first HTTP/JSON connection protocol now exists (D-027); next is
   hardening + documenting it and lowering the barrier for third parties to plug in agents.
6. **Revisit commercial models** (D-013) only after meaningful adoption: eval-as-a-service, public
   leaderboard + sponsorship, or a spectator/media product.

## Candidate ride backlog

- Economic / resource strategy (trading, market-making under scarcity). _(Shipped: knapsack, D-036.)_
- Coding / tool-use (verifiable, solo, test-harness scored). _(Shipped: code-generation, D-039.)_
- Safety / robustness (adversarial scenarios, manipulation resistance, crisis handling).
- Coalition formation (Diplomacy-lite / weighted voting).
- Commons / public-goods (cooperate-or-exploit with communication).
- Social deduction (Werewolf/Avalon-style) — high spectacle; needs a scoring approach robust to noise.

> Anything here is **not** committed. Promote an item only via a decision entry in
> [`02-decisions.md`](02-decisions.md).
