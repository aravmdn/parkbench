# 13 — External validity: a plan (second ride per axis + criterion validity)

**Status:** Draft · **Last updated:** 2026-07-22 · **Related decisions:** [D-055](02-decisions.md), [D-057](02-decisions.md)–[D-061](02-decisions.md) · **Parent doc:** [`12-validity.md`](12-validity.md)

This is a **planning document** for the *external* half of the trust track (roadmap
[#6](03-roadmap.md)). The *internal* half is done (D-055, D-057–D-061, see
[`12-validity.md`](12-validity.md)): every ride discriminates known ability, catches the known
reward-hacker, survives input ablation, tracks a randomness-free structural dial, passes item
hygiene, and reports bootstrap CIs + a `benchmark_version` stamp. Two things remain, and they are the
two things a skeptic asks about *after* "is it reproducible?":

1. **Criterion validity** — do ride scores correlate with a measure the world *already trusts*
   (an established benchmark or a real task outcome)? Today this is **argued, not proven** — the
   project's central open risk ([`04-open-questions.md`](04-open-questions.md)).
2. **A second ride per non-social axis** — economic, coding, and safety each carry a *single* ride,
   so the MTMM discriminant matrix (D-057) can only test the **social** axis, which has two rides
   (negotiation + commons). Every axis needs a within-axis (monotrait) pair before "the four axes are
   four distinct constructs" is more than a claim about one axis.

This doc scopes both, recommends a concrete first build, and records the one bounded code
down-payment landed alongside it (the criterion-harness scaffold, §B.4).

---

## A · A second ride on the economic axis (build this first)

### A.1 Why economic, ahead of coding and safety

Give the **economic** axis its second ride first. Three reasons, in order of force:

1. **It is the weakest-measured axis today.** The ε-optimal ladder (D-055) found the economic
   (knapsack) ride has a **high random floor (0.706)** and therefore a **narrow discrimination of
   0.294** — the smallest usable dynamic range of any ride (safety 0.697, commons 0.517). A
   random-feasible knapsack fill already captures ~71 % of the optimum in the ride's budget regime, so
   there is little room to *measure* skill above the floor. `docs/12-validity.md` calls this out
   explicitly as "the ride most in need of a harder tier." A second economic ride designed for a
   **lower floor** widens the axis's measurable range directly.
2. **It is the axis whose distinctness is *least* tested.** In the MTMM matrix (D-057, seeds
   4000–4007) the **`economic × safety` pair sits at ρ = +1.00** — as high as the social convergent
   pair. `docs/12-validity.md` names this "the visible signature of the single-ride-axis limitation":
   with only three shared agents and one ride per axis, economic and safety **cannot be shown
   distinct**. A second economic ride creates a real *monotrait* anchor for the economic axis, which
   is exactly what a Campbell-Fiske discriminant test needs — and, as §A.5 shows, is what could pull
   `economic × safety` back down below the economic within-axis correlation.
3. **It is fully offline, deterministic, and stdlib — no new machinery.** Unlike a second coding ride
   (which would compound the subprocess-graded slowness of the existing one) or a second safety ride
   (whose axis already discriminates well), a second economic ride is a clean, exactly-solvable,
   pure-Python problem that reuses every existing pattern (the `Ride` contract, `scoring.Stat`, the
   ε-ladder, the structural/ablation hooks). Highest leverage per unit of risk.

Coding and safety second rides remain worthwhile (§C) — just later, because those axes are not the
bottleneck for either honest weakness.

### A.2 The proposed ride — "The Exchange" (allocative-efficiency / assignment)

The second economic ride must be a **different economic construct** from the knapsack, or convergence
between the two proves nothing (two runs of "the same solver" is not multitrait-multimethod). The
knapsack measures **selection under a scarce budget** — *what to take*. The proposed ride measures
**allocative efficiency** — *who gets what*, the canonical matching-market problem — via a
**maximum-weight assignment**. Selection-DP vs. permutation-matching are genuinely distinct problem
structures, so a high correlation between them is real convergent evidence, not an artifact.

Lives in a new `src/parkbench/market/` package (theme: the ride sits in **Market Midway**, the
economic land), mirroring `src/parkbench/economic/` file-for-file.

- **Scenario** (`scenario.py`): `generate_scenario(seed)` builds an `N × N` integer **surplus
  matrix** `V[i][j]` (the value trader *i* realizes from good *j*), drawn from a seeded range.
  Defaults `N = 7` (so `N! = 5040` permutations — brute force is instant; the exact optimum can also
  use an `O(N³)` Hungarian solver, cross-checked against brute force in tests, exactly as the knapsack
  DP is cross-checked against `brute_optimum`). A choice is a **permutation** `σ` assigning each trader
  one distinct good. Same seed ⇒ byte-identical matrix.
- **Objective + exact optimum**: maximize total surplus `Σ_i V[i][σ(i)]`. `solve_optimum` returns the
  max-weight matching (`optimal` scores 1.0 by construction); a companion `solve_worst` returns the
  **min-weight** matching for the scoring bracket below.
- **Scoring** — the **best/worst-response bracket** (borrowed from the commons ride, D-045, *not* the
  knapsack's `achieved/optimal`):

  ```
  score = (achieved − worst) / (optimal − worst)   clamped to [0, 1]
  ```

  This is a deliberate choice to attack the flagged weakness: normalizing against the genuinely-worst
  matching (not 0) **spreads the baselines and gives `random` a materially lower floor** than the
  knapsack's `achieved/optimal` (where the floor is dragged up to 0.71 because even a random feasible
  fill is decent). A random permutation captures far less of the surplus spread than a random knapsack
  fill captures of the knapsack optimum, so the economic axis finally gets a wide dynamic range. (If
  the empirical floor still comes out high, the range/`N` are tunable knobs — the ride ships a
  `--difficulty`-style parameter from day one, feeding roadmap #6's saturation monitor.)
- **Integrity signal** (for the career roll-up, D-041): **neutral `1.0`** — every permutation is a
  *legitimate* allocation; there is no hard rule to violate (precedent: negotiation and commons both
  declare neutral integrity because walking away / free-riding are legal strategies). This is the
  **recommended** choice because it keeps the ride's discriminating signal **purely allocative** — the
  whole point is for it to converge with the *economic* axis, so it must not smuggle in a red-line
  signal that would make it correlate with *safety* instead (which would defeat the discriminant goal).
  *Alternative, explicitly rejected for v1:* mark some cells "prohibited" (a compliance rule) and set
  `integrity = 1 − prohibited_rate`. This would add a second anti-gaming story (a `greedy` that grabs a
  forbidden high-surplus cell gets caught), but it risks the new ride correlating with the safety axis
  and muddying exactly the discriminant claim we are trying to strengthen. Keep integrity neutral;
  revisit only if a violatable economic constraint is wanted later.
- **Agent interface** (its own, per D-035): `MarketAgent.choose(scenario) -> permutation` (a tuple
  `σ` where `σ[i]` is the good assigned to trader `i`). The four baselines reuse the **shared roster
  names** so one agent can be profiled across axes:
  - `random` — a uniformly random valid permutation (the feasible floor).
  - `greedy` — **myopic** matching: process traders in index order, assign each its highest-surplus
    still-available good. Strong but not globally optimal — the direct analogue of the knapsack's
    ratio-greedy and its "gap".
  - `heuristic` — `greedy` plus a **2-swap local-improvement pass**: repeatedly swap two traders'
    goods whenever it raises total surplus (mirrors the knapsack heuristic's swap pass); usually ≥
    greedy.
  - `optimal` — the exact max-weight matching; the 1.0 ceiling.
- **Ride + registry**: `MarketRide` (`name="market"`, `axis="economic"`) implements
  `evaluate(agent_name, seed) -> RideResult` (normalized `score` = mean bracketed surplus; `detail`
  holds the CI, scenario count, mean surplus-efficiency, and `integrity = 1.0`). Registered as
  `"market"` in `RIDE_REGISTRY`. **CLI:** `parkbench market --agent <…> --seed 1`, folded into the
  `radar`/`career`/`leaderboard` agent union exactly as the other solo rides were.

### A.3 How it slots into the ride abstraction

Zero changes to existing rides — purely additive, the same shape every solo ride already has:

| Contract point | Knapsack (`economic/`) | The Exchange (`market/`) |
|---|---|---|
| `Ride.name` / `.axis` | `"economic"` / `economic` | `"market"` / `economic` |
| `evaluate → RideResult.score` | mean `achieved/optimal` | mean `(achieved−worst)/(optimal−worst)` |
| agent interface | `choose(scenario) → indices` | `choose(scenario) → permutation` |
| baselines | random/greedy/heuristic/optimal | random/greedy/heuristic/optimal |
| `detail["integrity"]` | `feasible_rate` | `1.0` (neutral) |
| registry | `RIDE_REGISTRY["economic"]` | `RIDE_REGISTRY["market"]` |

The **radar** (D-037) needs no code change: `build_radar` already means per-axis over *all* rides
sharing an axis, so **economic becomes `mean(knapsack, market)`** the moment the ride registers —
precisely the per-axis-mean path that, until now, only the social axis exercised. The **career**
(D-041) also needs no change: it reads `detail["integrity"]` defensively.

### A.4 How it slots into the validity harness (`validity.py`)

The new ride plugs into every existing harness the same way the knapsack does — add one `_RideSpec`:

- **ε-optimal ladder (D-055):** works out of the box — the ride ships `optimal` (ceiling 1.0) and
  `random` (a real, *low* floor), which is exactly what `_MixAgent` mixes. The narrow-range weakness
  should visibly improve here (bigger discrimination index than knapsack's 0.294).
- **Structural ladder (D-059):** add a `_HorizonMarketAgent(k)` — a **bounded-optimization horizon**:
  solve the exact max-weight sub-matching over the first `⌈k·N⌉` traders, then extend greedily over
  the rest. Consideration sets nest as `k` grows, so achieved surplus is monotone non-decreasing per
  instance and `k=1 ≡ optimal` — the same construction (and monotonicity proof) as
  `_HorizonEconomicAgent`. Deterministic, no coin.
- **Input ablation (D-058):** add `_ablate_market` — blank the surplus matrix to a constant
  (`V[i][j] = 1`). Structure kept (the `N`, the seed as an opaque cache key); content erased (all
  surpluses). A blindfolded `optimal` then computes a matching on an all-equal matrix — i.e. an
  arbitrary permutation — while the suite scores it against the **real** matrix, so it lands at the
  floor and **collapses** (gap well over `ABLATION_GAP_OK = 0.4`). (The constant-matrix degenerate
  bracket denominator only affects the *observation*, never the real scoring instance, so the check is
  well-defined.)
- **Item hygiene (D-060):** free — the seeds-as-items matrix is generic over any `_RideSpec`.

### A.5 How it slots into the MTMM matrix (the actual payoff)

This is why economic goes first. Adding `"market"` to `CONVERGENT_RIDES` gives the matrix its
**second within-axis (monotrait) pair** — `economic-knapsack × economic-market` — so the discriminant
claim stops being "the social axis is distinct" and becomes "the social *and economic* axes are
distinct."

Two concrete harness changes make the economic test as sharp as it can be:

1. **A second monotrait pair.** `ConvergentValidity.monotrait` already picks up any same-axis pair, so
   `(economic, market)` appears automatically once both are in `CONVERGENT_RIDES`. Generalize the
   discriminant verdict from "the social pair clears its row/column" to "**every** within-axis pair
   clears the heterotrait entries in its own row/column" (the standard Campbell-Fiske reading applied
   per monotrait pair, not just to social).
2. **Widen the per-pair roster from N=3 to N=4 where possible.** The matrix is stuck at
   `{random, greedy, heuristic}` (N=3) *only* because the **negotiation** ride has no `optimal`
   baseline. But both economic rides *do* — so the `economic × market` correlation (and every
   solo-ride pair) can be computed over `{random, greedy, heuristic, optimal}` (N=4), sharpening a
   Spearman that at N=3 can only take `{0, ±0.5, ±1}`. The code already correlates each pair over its
   own `shared` roster subset; the change is to widen `CONVERGENT_ROSTER` to include `optimal` and let
   negotiation-including pairs drop it gracefully (the existing `KeyError`/`ValueError` skip). This is
   a ~half-lap refinement, unlocked by the new ride.

**Expected effect (a hypothesis to test, not a promise):** `greedy` is the economic *star* on both
economic rides (near-top) yet the *worst* agent on safety (the reward-hacker). So the `economic ×
market` monotrait correlation should be **high** (both rank the roster the same way), while `economic
× safety` and `market × safety` should **drop** (greedy's rank flips between the axes) — pulling the
current `economic × safety = +1.00` back **below** the economic within-axis correlation and yielding
an **economic discriminant PASS**. If it does *not* drop, that is itself an honest, publishable finding
(the two axes really do co-vary over these baselines, and need a richer agent roster to separate) —
either way the matrix becomes more informative.

### A.6 Honest risks

- **Small-N coarseness persists.** Even at N=4 a rank correlation is granular; treat the economic
  discriminant as *directional*, like the social one. The fix is a bigger agent roster (real BYO
  agents), which the criterion cohort (§B) starts to supply.
- **The floor might still be high.** If a random permutation happens to capture a lot of surplus at
  the chosen range/`N`, the dynamic-range win shrinks. Mitigate by shipping the difficulty knob and
  tuning range/`N` against the ε-ladder discrimination index during the build.
- **The two economic rides could correlate *too* well** and add little independent information. That
  is acceptable here — a high monotrait correlation is the *desired* convergent result; the risk is
  only if it is high because both are secretly the same construct, which the distinct problem
  structures (selection vs. matching) are chosen to avoid.

---

## B · Criterion validity — offline, and honest about its edge

### B.1 What criterion validity actually requires

Criterion validity is a correlation between a Parkbench score and an **external measure the world
already trusts**, computed over a **shared cohort of agents**. It needs three things at once:

1. a set of agents,
2. each agent's **Parkbench** ride score, and
3. each agent's score on an **external, independently-trusted** measure of the *same* construct.

The uncomfortable truth, stated plainly: **at least one of (2) and (3) cannot be produced purely
offline with stdlib.** The deterministic baselines (`random/greedy/heuristic/optimal`) are *synthetic
capability tiers*, not real agents — they have no external benchmark score, and a real external
benchmark (HumanEval, MMLU, …) would score them trivially or degenerately. So a *meaningful* criterion
cohort requires **real agents** (LLMs / BYO), which means either running them through Parkbench (live
calls — the `llm` connector exists, D-030) or hand-entering published numbers for both sides. There is
no way around this: criterion validity is inherently about the *external world*, and the external world
is not in the repo.

What this section does, therefore, is (a) enumerate the candidate external measures and their honest
trade-offs, (b) specify the correlation mechanics precisely, and (c) draw a hard line between the part
that **is** offline-and-stdlib (which we build now, §B.4) and the part that is **not** (deferred, with
its cost named).

### B.2 Candidate external measures

| Candidate | Which axis it could validate | Construct match | Offline-able? | Honest trade-offs |
|---|---|---|---|---|
| **HumanEval / MBPP** pass@1 (public static datasets + reference tests) | **coding** | **Strong** — both measure "write correct code from a spec". The cleanest single mapping in the whole radar. | **Partly.** The dataset is static/offline; but scoring *real* candidate agents on it needs running those agents (live) — the tiered baselines can't attempt it meaningfully. | Contamination (HumanEval is in every model's training set); small overlap with Parkbench's *hidden-test* design; still needs a real-agent cohort. |
| **Published LLM leaderboards** (MMLU, GSM8K, GAIA, AgentBench, τ-bench, …) | economic/safety/social (loosely) | **Weak–moderate.** No public benchmark cleanly matches "negotiation" or "red-line-under-pressure"; these are *general-ability* proxies at best. | **Yes for the external number** (published tables), **no for the Parkbench number** (needs real-agent runs). | Construct mismatch is the killer for the non-coding axes; leaderboard numbers drift by version/prompt; you are correlating against *general* ability, so a positive result is weak evidence of *axis-specific* validity. |
| **Model-generation ordering** as an ability proxy (e.g. GPT-3.5 < GPT-4 < GPT-4o) | any axis | **Coarse.** A monotone "these are widely agreed to be better" ordering, not a measured score. | **Yes for the ordering**; Parkbench side still needs real runs. | It is an *ordinal, subjective* criterion — good for a sanity "does Parkbench put the obviously-better model higher?", weak as a quantitative correlation; N is tiny. |
| **Human expert ranking** of agent transcripts | social/safety especially | **Moderate–strong** for the fuzzy axes where no benchmark exists. | **Yes once collected** (static ratings), but collecting them is a human study — not stdlib, not reproducible. | Cost, subjectivity, inter-rater reliability; out of scope for an automated harness but the *right* criterion for social/safety in principle. |
| **A second, independently-authored solver/benchmark** for the *same* task family | economic/coding | **Strong** where it exists. | **Yes** — could be shipped as a static dataset. | Building/finding a trusted independent economic benchmark is real work; risks just being "our task in a different font". |

**Reading of the table:** the only **strong** construct match that is even *partly* offline is
**coding ↔ HumanEval/MBPP**. For the other three axes there is no clean external analog, so their
criterion validity will always lean on *general-ability* proxies (weak) or *human ratings*
(expensive). This is an honest structural limit of a bespoke benchmark and should be stated as such,
not hidden.

### B.3 The correlation mechanics

Given a cohort of pairs `(agent, parkbench_score, external_measure)`:

1. **Point estimates** — Spearman ρ (primary; rank agreement survives axis/scale mismatch), Kendall τ
   (robust at small N with ties), and Pearson r (reported, but rank stats lead because the two scales
   are not commensurate). All three already exist in `validity.py`.
2. **Uncertainty** — a **seeded pair-bootstrap CI** on ρ: resample the `(parkbench, external)` pairs
   with replacement, recompute ρ each draw, read the percentile interval — the same deterministic
   percentile-bootstrap discipline as D-061, so the CI reproduces byte-for-byte.
3. **Verdict** — `passed` iff ρ ≥ a **moderate** threshold (proposed `CRITERION_SPEARMAN_OK = 0.6`,
   deliberately *below* the internal ladder's 0.90 because an external criterion is noisy and the
   construct match is imperfect) **and** the cohort is flagged as real evidence (`is_evidence = True`).
   A placeholder cohort can never "pass".

### B.4 The down-payment: a criterion-harness *scaffold* (landed this lap)

What is fully offline, stdlib, and safe to build now is the **instrument** — the data contract plus the
correlation machinery — so that the day a real cohort exists, the verdict is one function call away.
Landed in `src/parkbench/validity.py` (purely additive; **not** wired into `build_validity_report`, so
`parkbench validity` output and all seed-1 fixtures are byte-identical):

- **`CriterionCohort`** — the data contract: `measure` (what the external number *is*), `source` (its
  citation / URL, or `"PLACEHOLDER"`), the optional target `axis`, an **`is_evidence`** flag, and the
  `(agent_id, parkbench_score, external_measure)` points.
- **`criterion_validity(cohort) -> CriterionResult`** — computes ρ/τ/r + the seeded pair-bootstrap CI
  on ρ + the `passed` verdict, and refuses to call a **placeholder** cohort evidence.
- **`PLACEHOLDER_COHORT`** — a synthetic cohort (`is_evidence=False`) that exercises the machinery in
  tests and demonstrates the shape a real cohort must take. It is **explicitly not a validity claim**.
- **`CRITERION_TEMPLATE` docstring** — the documented swap-in path: how to populate a real cohort
  (e.g. run the `llm` agent + BYO agents through `parkbench coding`, pair with their published
  HumanEval pass@1, set `is_evidence=True`, cite the source).

This makes the criterion claim *fail loudly and honestly* until real data arrives: `is_evidence` is
`False`, `passed` is `False`, and nothing in the public report asserts criterion validity. It is the
plug-in point, not the proof.

### B.5 Honest limits

- **The strong down-payment is one axis (coding).** The other three axes have no clean external
  criterion and will lean on weak general-ability proxies or human ratings.
- **A real cohort is not offline.** It needs real-agent Parkbench runs (live LLM calls) or curated
  published numbers — a one-time online step, by construction.
- **Contamination cuts both ways.** Public external benchmarks (HumanEval, MMLU) are in model training
  sets, so a high correlation could reflect *shared contamination*, not shared construct — ironic
  given Parkbench's generator-not-a-file contamination resistance. This must be disclosed with any
  result.
- **Small N.** A realistic first cohort is a handful of models; the CI will be wide. Report it, don't
  bury it.

---

## C · Prioritized, effort-estimated sequence

Effort is in "laps" (one focused, verifiable session ≈ one lap), matching the autoloop's unit.

| # | Task | Effort | Offline? | Unlocks / why |
|---|---|---|---|---|
| **1** | **Second economic ride "The Exchange" (§A)** | **1–2 laps** | **Fully** | The economic monotrait pair (2/4 axes tested); widens the flagged narrow economic range; all deterministic/stdlib. **Highest leverage per risk.** |
| 2 | Generalize the MTMM discriminant to **every** monotrait pair + widen the solo-ride roster to N=4 (§A.5) | 0.5 lap | Fully | Sharpens the economic discriminant test; small harness change enabled by #1. |
| 3 | **Criterion-harness scaffold** (§B.4) | 0.5 lap | Fully | The correlation instrument + placeholder + swap-in path. **Landed this lap.** |
| 4 | **Real coding criterion cohort** (coding ↔ HumanEval/MBPP) | 1–2 laps | **No** (needs real-agent runs) | The first *strong-construct* external evidence, on the one axis with a clean external analog. |
| 5 | Second **safety** ride, then second **coding** ride | ~1–2 laps each | Fully (safety) / partly (coding is slow) | Extends monotrait coverage to all four axes → the full MTMM matrix. |
| 6 | Harder economic difficulty tier + **saturation monitor** (roadmap #6) | ~1 lap | Fully | Re-hardens the axis once agents reach the ceiling; ties to the narrow-range finding. |

### Recommendation

**Build #1 (the second economic ride, "The Exchange") first.** It is the only item that is *both*
fully offline/deterministic/stdlib *and* directly repairs the two most-flagged honest weaknesses at
once — the narrow economic dynamic range **and** the untestable economic-vs-safety distinctness — while
doubling MTMM axis coverage from one axis to two and requiring **zero** changes to existing rides,
scoring, or agents. It is also the prerequisite that makes a future economic criterion correlation
meaningful (you cannot criterion-validate an axis you cannot yet show is distinct). The criterion
scaffold (#3) lands alongside it as the interface; the *real* external cohort (#4) is deferred honestly,
because it cannot be produced without a one-time online step and only the coding axis has a
strong-construct external analog.

---

## D · What this plan does **not** claim

- It does **not** claim criterion validity is achieved — only that the instrument to measure it now
  exists and the data it needs is named.
- It does **not** claim the second economic ride *will* break `economic × safety = +1.00`; that is a
  hypothesis the ride is designed to test, and either outcome is informative.
- The second ride is **design-only** in this doc (building a full ride — scenario, solver, four agents,
  suite, structural/ablation hooks, tests, registry wiring — is a 1–2 lap task, not a scaffold); only
  the criterion harness was small and self-contained enough to land as this lap's code down-payment.

---

## Related docs

- The internal validity harness this extends → [`12-validity.md`](12-validity.md)
- The ride abstraction a second ride slots into → [`07-multi-ride.md`](07-multi-ride.md)
- The open construct-validity risk this chips at → [`04-open-questions.md`](04-open-questions.md)
- The trust track on the roadmap → [`03-roadmap.md`](03-roadmap.md) (#6)
