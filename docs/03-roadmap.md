# 03 — Roadmap

**Status:** Living · **Last updated:** 2026-05-31

Directional only — sequence and detail will firm up as v1 is built and learned from. v1 itself is in
[`01-v1-scope.md`](01-v1-scope.md).

## After v1 (rough order)

1. **Second ride → validate the radar with ≥2 axes.** Likely an **Economic/resource** ride — the
   closest sibling to negotiation, reusing the objective-payoff scoring. Proves the diagnostic
   profile concept with more than one data point. _(In progress, 2026-05-30: the ride abstraction
   landed (D-035); economic ride (D-036) + radar roll-up (D-037) underway.)_
2. **Fill out the four axes.** ✅ _Done (2026-05-31)._ The **Coding/tool-use** ride (D-039, solo
   code-generation, hidden-test scored) and the **Safety/robustness** ride (D-040, red-line under
   adversarial pressure — uses the "nudge"/injection mechanic as an adversarial probe) landed, so the
   **radar now spans all four axes** (social · economic · coding · safety).
3. **Introduce cross-ride "career."** ✅ _Done (2026-05-31)._ The **career** (D-041) is the first
   cross-ride coupling: every ride declares an `integrity` signal, **reputation = the product** of
   them, and **`career_score = mean_capability × reputation`** — so misconduct anywhere discounts
   capability everywhere (it deliberately reverses part of D-008, logged in D-041). It makes a
   reward-hacker pay: `greedy`, the economic star, lands last (below `random`) because its red-line
   violations collapse its reputation. See [`07-multi-ride.md`](07-multi-ride.md).
4. **Theming + spectator product.** _Started (2026-05-31):_ a **career leaderboard** (D-042,
   `parkbench leaderboard`) ranks agents by career score — the first watchable surface. Still to do:
   apply the creative skin and a career/radar-aware static replay/leaderboard viewer for mindshare.
5. **Grow the BYO ecosystem.** A first HTTP/JSON connection protocol now exists (D-027); next is
   hardening + documenting it and lowering the barrier for third parties to plug in agents.
6. **Revisit commercial models** (D-013) only after meaningful adoption: eval-as-a-service, public
   leaderboard + sponsorship, or a spectator/media product.

## Candidate ride backlog

- Economic / resource strategy (trading, market-making under scarcity). _(Shipped: knapsack, D-036.)_
- Coding / tool-use (verifiable, solo, test-harness scored). _(Shipped: code-generation, D-039.)_
- Safety / robustness (adversarial scenarios, manipulation resistance, crisis handling).
  _(Shipped: red-line under adversarial pressure, D-040.)_
- Coalition formation (Diplomacy-lite / weighted voting).
- Commons / public-goods (cooperate-or-exploit with communication).
- Social deduction (Werewolf/Avalon-style) — high spectacle; needs a scoring approach robust to noise.

> Anything here is **not** committed. Promote an item only via a decision entry in
> [`02-decisions.md`](02-decisions.md).
