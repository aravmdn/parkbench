# 03 — Roadmap

**Status:** Living · **Last updated:** 2026-06-02

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
4. **Theming + spectator product.** _Well underway:_ a **career leaderboard** (D-042,
   `parkbench leaderboard`) ranks agents by career score; a static, zero-dependency
   **diagnostic-profile viewer** (D-044, `viewer/profiles.html`) renders the radar (inline-SVG),
   career (trust-collapse), and leaderboard (reward-hacker callout) from the `--json` outputs; and the
   **creative skin is now applied** (D-046, 2026-06-03) as a presentation-only layer — `theme.py`
   (lands = axes, attractions = rides), a `parkbench map` command, and a themed landing page
   `viewer/park.html`. See [`08-theming.md`](08-theming.md). Still to do: richer per-ride art and
   possibly **live/served profiles** for mindshare.
5. **Grow the BYO ecosystem.** A first HTTP/JSON connection protocol exists (D-027), and the coding
   harness is now **sandboxed + time-bounded** (D-043, subprocess + wall-clock timeout) so it is safe
   to point at untrusted BYO code. Next: document/harden the protocol, lower the barrier for third
   parties, and add a **full OS sandbox** (FS/network/resource confinement) for untrusted code.
6. **Revisit commercial models** (D-013) only after meaningful adoption: eval-as-a-service, public
   leaderboard + sponsorship, or a spectator/media product.

## Candidate ride backlog

- Economic / resource strategy (trading, market-making under scarcity). _(Shipped: knapsack, D-036.)_
- Coding / tool-use (verifiable, solo, test-harness scored). _(Shipped: code-generation, D-039.)_
- Safety / robustness (adversarial scenarios, manipulation resistance, crisis handling).
  _(Shipped: red-line under adversarial pressure, D-040.)_
- Coalition formation (Diplomacy-lite / weighted voting).
- Commons / public-goods (cooperate-or-exploit). _(Shipped: multi-agent public-goods game, D-045 —
  the second social-axis ride; first to exercise the radar's per-axis mean.)_
- Social deduction (Werewolf/Avalon-style) — high spectacle; needs a scoring approach robust to noise.

> Anything here is **not** committed. Promote an item only via a decision entry in
> [`02-decisions.md`](02-decisions.md).
