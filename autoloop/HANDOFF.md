# HANDOFF — the live baton

> The single source of truth for what's happening **right now**. Updated **write-ahead** (after every
> meaningful step, before any long op) — a usage cutoff can kill a session mid-step. **Git is ground
> truth for work done; this file is ground truth for intent / next action.** See
> [`../docs/10-autoloop.md`](../docs/10-autoloop.md) for the protocol.

---

**Updated:** 2026-07-08
**Loop state:** IDLE

**Active task:** — (none)
**Acceptance criteria:** —
**Task branch:** — (none active; local-driver laps use `autoloop/task-<slug>` → land on `main`, D-051)
**Tree state:** clean · on `main`
**Last durable commit:** (see `git log -1`)

**Last landed (this session):** `convergent-validity` (D-057) — a convergent/discriminant MTMM matrix
in `parkbench validity` (+`--json`). Over the shared roster `{random,greedy,heuristic}` (the only set
scorable on every ride, since negotiation has no `optimal`), the two social rides converge
(negotiation×commons ρ=+1.00) and that exceeds every social cross-axis ρ=+0.50 ⇒ discriminant PASS
(Campbell-Fiske). Purely additive: pytest 195 green (+6), baselines byte-identical. Honest limits (N=3;
only social has a within-axis pair; economic×safety also ties at +1.00; ≥8 seeds needed) documented in
`docs/12-validity.md`.

**Loop / active driver (D-056):** the owner activated the **local `/loop` driver** (D-051 model) as the
active driver on 2026-07-08. Setup + the standing driver/worker prompt: `autoloop/LOCAL_DRIVER_PROMPT.md`.
Local laps work a `autoloop/task-<slug>` branch and **land on `main` gate-free**. The **hourly cloud-cron
routine (D-054) remains DESIGNED + DOCUMENTED but UNARMED** (its prompt is `autoloop/ROUTINE_PROMPT.md`;
arming is still blocked on owner approval of the scheduling MCP call) — use it only if switching back to
the cloud model. Note: the last recorded laps (through `world-signposts`, 2026-07-04) ran on the cloud
branch `claude/next-tasks-j7f20o`; the validity harness (D-055) + LLM-fallback landed as manual sessions,
not autoloop laps.

**NEXT ACTION:** Loop is IDLE. The backlog is **not empty** — pull the TOP unchecked task, now
**`ablation-baseline`** (trust track, roadmap #6, Tier A): re-run the best agent on a **blanked/degraded
observation** and require its score to collapse (the single best shortcut detector). Needs a per-ride
"degraded scenario" hook. **Done when:** each ride reports an ablation gap and a test asserts
`score_ablated << score_full`; keep `pytest` green + baselines byte-identical (measurement is additive —
do NOT edit scoring/agent/ride logic to move numbers). Create branch `autoloop/task-ablation-baseline`
and begin. (After the trust track drains, a refill can decompose the next *visual* chunk — live/served
profiles, multiple trainers, a BYO-agent connector.)

**Blockers / needs-owner:** none
