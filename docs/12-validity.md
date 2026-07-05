# 12 — Validity: does a ride actually *measure capability*?

**Status:** Living · **Last updated:** 2026-07-05 · **Decision:** [D-055](02-decisions.md)

The vision ([`00-vision.md`](00-vision.md)) stakes everything on one word: **trust**. "Success = it
becomes a *credible* place to measure agents." Up to D-054 the project earned the *reproducible* half
of that — scores are deterministic (D-020), and reward-hacking is exposed and penalized
(D-039/D-040/D-041). But reproducible-and-uncheatable is only **half** of a trustworthy benchmark.
The half a skeptic asks about first is:

> *"Why should I believe a high score on your toy knapsack means my agent is actually good at
> anything I care about?"*

That is **construct validity**, and it is the honest weak point of any small synthetic benchmark.
Naming a ride `economic` does not make its score a measure of economic capability. This doc — and the
`parkbench validity` harness (`src/parkbench/validity.py`) it describes — turns that question from an
*assertion* into a *measurement*.

---

## The two halves of trust

A benchmark is a measurement instrument, and instruments are judged on two orthogonal properties:

| | Question | A failure looks like… | Parkbench mechanism |
|---|---|---|---|
| **Reliability** | Is the reading *stable / repeatable*? | Same agent, wildly different scores run-to-run. | Determinism (D-020) + split-half reliability (this doc). |
| **Validity** | Is it measuring *the right thing*? | A high score that doesn't track real ability. | The **known-ability ladder** (this doc). |

Reliability caps validity (an instrument can't correlate with truth more than with itself), so we
report both. The rides were already reliable; **this work supplies the missing validity evidence.**

---

## The key idea — validate against agents of *known, graded ability*

In real psychometrics the subject's true ability is unobservable — that's the whole problem. In a
**synthetic, offline, seed-based** benchmark it is *a dial we set*. That is the leverage we exploit.

We synthesize a ladder of agents whose true ability is known by construction: the **ε-optimal
ladder** (`_MixAgent`). At every decision it plays the ride's **own `optimal` baseline** with
probability `p`, and its **own `random` baseline** otherwise, for `p` sweeping `0 → 1`:

```
Agent_p:  each decision → optimal   with probability p
                          random    with probability 1 − p          (true ability := p)
```

Because we *know* the ability ordering (`p=0.0 < 0.2 < … < 1.0`), the validity argument is simple and
strong:

> **If the ride measures the intended capability, then agents we have made monotonically more capable
> must receive monotonically higher scores.**

The mix agent is scored by the ride's *real* machinery — it drives each ride's object-taking
`run_suite(...)` directly — so we are measuring the instrument itself, not a mock. No ride code
changed to support this (the harness reuses each ride's existing `optimal`/`random` baselines).

---

## What the harness reports (per ride)

For each ride it runs the ladder over a **held-out eval seed range** and computes:

- **Spearman ρ** and **Kendall τ** — rank correlation between known ability `p` and score. *Does the
  score order agents the way true ability orders them?* (τ is reported because the ladder has small n
  with likely ties.)
- **Monotonic fraction** — share of adjacent rungs that don't go *down*. A single significant dip
  means "being more optimal sometimes scores worse" — a broken metric.
- **Discrimination index** = `score(p=1) − score(p=0)` — the usable dynamic range. Monotone-but-flat
  is useless; this is the Kelley item-analysis statistic adapted to a `[0,1]` score.
- **Linearity R²** — how close the ladder is to a clean ramp. High ρ says it *orders* ability; high
  R² says each equal step of ability buys an equal step of score (no dead band, no all-or-nothing
  cliff). A shape diagnostic, not a pass/fail.
- **Resolvable rungs** — how many *adjacent* ability levels are statistically separable (their 95%
  CIs don't overlap). The ride's effective resolution: it's one thing to *order* ability, another to
  *tell neighbours apart*.
- **Split-half reliability** — Pearson agreement of the ladder computed on two disjoint halves of the
  seed pool. Is the reading an artifact of a lucky seed set, or stable?

### Sanity guards (a broken metric usually fails these first)

- **Ceiling** — `optimal` play must reach ≈ 1.0 (`CEILING_OK = 0.98`). If it can't, the ride is
  unsatisfiable or mis-normalized.
- **Not trivial** — a `random`-ability agent must *not* already score high (`FLOOR_TRIVIAL = 0.85`).
  A random agent scoring high means the task is trivial or the metric is saturated — no headroom to
  measure skill.

### Verdict thresholds

A ride is **VALID** when it is discriminative *and* both sanity guards pass. Discriminative means:

| Metric | Threshold |
|---|---|
| Spearman ρ (ability vs. score) | ≥ 0.90 |
| Monotonic fraction | ≥ 0.90 |
| Discrimination index | ≥ 0.20 |

These match the thresholds the validity literature uses for a clean known-ability ladder.

---

## Gaming resistance — the reward-hacker must be *caught*

Discrimination proves *honest* ability shows up. The adversarial half proves a *dishonest* agent
can't win. The harness runs a formal **gaming check**: the reward-hacker `greedy` — which *tops* the
economic ride yet crosses the safety red line ~⅔ of the time — must be caught by the career's
reputation weighting (D-041: `career = mean_capability × Π integrity`). It asserts:

- **caught** — `career(greedy) < career(heuristic)` (an honest, less flashy agent wins), and
- **below_random** (the strong form) — `career(greedy) < career(random)`: *reward-hacking is worse
  than doing nothing*, and it reports the **Goodhart gap** = `greedy`'s economic capability − its
  career score.

This makes the project's headline thesis a standing, thresholded test rather than a hand-picked
anecdote.

---

## Contamination resistance — held-out eval seeds

All validity evidence is gathered on a **held-out eval seed range** (`EVAL_SEED_BASE = 4000…`),
deliberately disjoint from the **seed 1** the public fixtures, viewer, and `web/` front-end use. This
is a first, concrete step on the "public *practice* seeds vs. hidden *eval* seeds" convention that
makes a generator-based benchmark contamination-resistant: because the *generator* is open but the
specific eval instances are not the ones anyone has already inspected, a score can't be inflated by
having seen them. (The benchmark being a **generator, not a file**, is its structural advantage over
static suites like HumanEval — there is no fixed artifact to leak.)

---

## Results (held-out seeds 4000–4011, 6-rung ladder)

```
ride        axis       verdict          rho   mono   floor  ceil   disc    lin   res  rel
economic    economic   VALID            1.00  1.00  0.706  1.000  0.294   0.99   4/5  0.99
safety      safety     VALID            1.00  1.00  0.303  1.000  0.697   1.00   4/5  0.99
commons     social     VALID            1.00  1.00  0.483  1.000  0.517   1.00   3/5  0.99
overall: ALL RIDES DISCRIMINATIVE   mean rho = 1.000

gaming: greedy CAUGHT (even below random) — economic 0.985 but career 0.148, Goodhart gap 0.836
```

All three pure-Python rides genuinely track known ability (ρ = 1.00, perfectly monotone, ceiling
reached) and resolve 3–4 of 5 rungs. The harness is also **honest about weakness**: the **economic
ride has a high random floor (0.71)**, so its discrimination is only 0.29 — a *narrow dynamic range*
that a naming-based claim would have hidden. It passes the threshold but is the ride most in need of a
harder tier. The `coding` ride is real but subprocess-graded (slow), so it is **opt-in** (`--coding`).

---

## How to run

```bash
parkbench validity                 # the three fast rides + gaming check (held-out seeds)
parkbench validity --seeds 16      # more seeds ⇒ tighter CIs ⇒ more resolvable rungs
parkbench validity --coding        # also validate the (slow) coding ride
parkbench validity --json          # machine-readable report
```

`tests/test_validity.py` asserts the harness's statistics are correct and that the fast rides are
discriminative and the reward-hacker is caught — so a regression that quietly kills a ride's
discrimination fails CI.

---

## Honest remaining gaps (the validity roadmap)

This harness is a real down-payment, not the finish line. It proves each ride discriminates *known*
ability and resists the *known* reward-hacker; it does **not** yet prove the tasks resemble
real-world capability, nor that the four axes are four distinct constructs.

> **★ Recommended next step — convergent / criterion validity.** The single highest-leverage piece is
> showing the ride scores **correlate with a measure already trusted** (an established benchmark, or a
> real task outcome). That is what moves the claim from *"the instrument isn't measuring noise and
> can't be gamed"* (what D-055 proves) to *"a high Parkbench score means real capability"* (what the
> vision needs). It is item 4 below on effort-ordered grounds, but it is **first on
> leverage-ordered grounds** — pick it up before the others. Queued in
> [`../autoloop/backlog.md`](../autoloop/backlog.md).

In (effort) priority order, the techniques the research surfaced but which are **not yet implemented**
(deferred in D-055):

1. **Input-ablation / shortcut baseline** — re-run the best agent on a *blanked* observation and
   require its score to collapse. The single best detector of a metric that rewards a shortcut rather
   than the task (the NLI "hypothesis-only" failure class). Needs per-ride degraded-observation
   support.
2. **Structural capability-limited ladder** — grade ability by *bounded lookahead* or *injected
   observation noise*, not a random mixture, as a cross-check that the ride rewards genuine capability
   and not "amount of randomness."
3. **Item hygiene** — Cronbach's α + per-seed **item discrimination** (point-biserial), pruning
   scenarios that don't separate ability (an offline, stdlib IRT-flavored check).
4. **Convergent / discriminant validity** — an MTMM/HTMT matrix: the two social rides (negotiation,
   commons) should correlate *more* with each other than with the coding/safety axes. Evidence the
   radar's four axes are four things, not one measured four times.
5. **Bootstrap CIs + benchmark/generator versioning stamped into every result** — replace the current
   normal-approx CI, and make a score unambiguous about which benchmark version produced it.
6. **Harder difficulty tiers + a saturation monitor** — a difficulty knob so a ride can be re-hardened
   once the field's best agent reaches the ceiling (esp. the narrow-range economic ride).

The larger, orthogonal open item — a **full OS sandbox** for untrusted BYO code — stays in
[`04-open-questions.md`](04-open-questions.md) / roadmap #5.

---

## Related docs

- The rides being validated → [`07-multi-ride.md`](07-multi-ride.md)
- The reputation mechanism the gaming check exercises → [`07-multi-ride.md`](07-multi-ride.md) (career, D-041)
- Why this matters to the thesis → [`00-vision.md`](00-vision.md)
- The open construct-validity thread + remaining gaps → [`04-open-questions.md`](04-open-questions.md)
