# 04 — Open Questions

**Status:** Living · **Last updated:** 2026-07-22

Questions still genuinely open. When one is resolved it becomes an entry in the decision log
([`02-decisions.md`](02-decisions.md)) and is listed under "Resolved" below.

_All four v1 follow-ups deferred from the core build (D-026) have now shipped — see **Resolved**
below (D-027–D-030)._

## Open — cross-cutting (post-v1)

- **Construct validity — do the rides measure the capabilities they are named for? (the central
  risk).** This is the deepest open question in the project and the one that most determines whether
  Parkbench is *trusted* (the vision's whole point) or merely *reproducible*. A ride called `economic`
  or `safety` asserts, by its name, that its `[0,1]` score is a measure of that capability — but the
  tasks are small, synthetic, hand-authored problems (a 12-item knapsack, 9 curated coding functions,
  scripted negotiation opponents), and naming is not evidence. Three things are now **down-paid**
  (D-055, [`12-validity.md`](12-validity.md)): *(a)* **discriminative validity** — each ride's score
  provably rises monotonically with **known, graded ability** (an ε-optimal ladder built from the
  ride's own optimal/random baselines; Spearman ρ = 1.0 on the three fast rides), so a ride that
  scored *noise* would be caught; *(b)* **gaming resistance** — a formal check that the reward-hacker
  is caught by the career's reputation weighting (`greedy` ranks below `random`; Goodhart gap 0.836);
  *(c)* a **held-out eval seed range** distinct from the public seed-1 fixtures (contamination
  down-payment). What stays **open** — the harder, honest gaps (prioritized in
  [`12-validity.md`](12-validity.md)): the tasks are not yet shown to *resemble real-world capability*
  (no convergent/criterion validity against an external, trusted measure); the **four axes are not yet
  shown to be four distinct constructs** (no MTMM/HTMT discriminant matrix — the radar could be
  measuring one thing four times); **input-ablation / shortcut** baselines are not yet run (the best
  detector of a metric rewarding a shortcut rather than the task); the ladder is only the *random-mix*
  kind, not a **structural** capability-limit (bounded lookahead / injected noise) cross-check; and
  there is no **item-hygiene** pass (Cronbach's α, per-seed discrimination pruning), no **bootstrap**
  CIs, and no **benchmark/generator versioning** stamped into results. Until at least convergent
  validity and the discriminant matrix exist, "a high Parkbench score means real capability" remains
  **argued, not proven** — the down-payment shows the instrument isn't measuring *noise* and can't be
  *gamed*, which is necessary but not sufficient.
- **Anti-gaming / reward-hacking safeguards** as more ride types are added. _Concrete down-payments
  have landed: the coding ride (D-039) uses **seed-randomized hidden tests** that defeat
  answer-memorization; the safety ride (D-040) is an explicit reward-hacking probe (crossing a red
  line scores 0 no matter the reward); and the **cross-ride career (D-041)** now makes misconduct
  anywhere discount capability everywhere — a reward-hacker's reputation collapse drags its whole
  career below an incompetent agent's, so reward-hacking is penalised across rides, not just exposed
  on one axis. **Time-bounding + process isolation of untrusted code has now landed (D-043)**: the
  coding harness runs candidate source in an isolated subprocess under a wall-clock timeout, so a
  hanging/crashing/malicious candidate just fails (score 0) instead of freezing or compromising the
  ride. **Environment + working-directory confinement has now landed too (D-048)**: the child runs
  with a minimal allowlisted environment (so untrusted code can't read parent secrets from
  `os.environ`) and in a throwaway working directory (so relative file writes don't touch the repo).
  Still open: a **full OS sandbox** for untrusted code (the child still has network access, can reach
  the filesystem by absolute path, runs with the parent's OS privileges, and has no CPU/memory/output
  caps — filesystem/network jails, resource limits, container/seccomp), folded into BYO-protocol
  hardening (roadmap #5); and continued vigilance as new ride types arrive._
- **A live, read-only profiles endpoint for the spectator surfaces.** The `live-profiles` task shipped
  its **static-export** half (D-062, `parkbench export-profiles` — one command regenerates every
  `web/`+`viewer/` fixture from the versioned CLI, so nothing is hand-copied). The other half — a small
  **read-only** HTTP endpoint that returns `radar`/`career`/`leaderboard` JSON on demand — is now
  **delivered** as the chunk-4 `serve-profiles-endpoint` task: **`parkbench serve --profiles`**
  (`src/parkbench/profiles_server.py`), a stdlib `http.server` subclass that serves the *verbatim* CLI
  producers' JSON (`build_radar`/`build_career`/`build_leaderboard`, same `benchmark_version` stamp) on
  `/radar?agent=…`, `/career?agent=…`, `/leaderboard`, and `/health` (404 unknown route, 400 bad
  agent/seed, 405 non-GET), covered by `tests/test_serve_profiles.py` (served JSON == CLI JSON).
  Presentation-only (D-012): serves existing producers' JSON, no scoring logic. *(Decision-log entry
  assigned on integration; documented in [`06-v1-architecture.md`](06-v1-architecture.md) and
  `web/README.md`.)* What still remains is only the **consuming** side — the `web/` app `fetch`ing this
  endpoint instead of importing a build-time fixture (the chunk-4 `web-fetch-profiles` task); the
  offline fixture path stays as the fallback.

## Resolved

- **2026-07-05** — **Discriminative validity + gaming resistance made measurable** resolved (partial —
  the discrimination/gaming *down-payment* on the open construct-validity question above) as **D-055**:
  a stdlib **validity harness** (`src/parkbench/validity.py`, `parkbench validity`) validates each ride
  against a **known-ability ε-optimal ladder** (Spearman/Kendall, monotonicity, discrimination,
  resolvable rungs, split-half reliability) with sanity guards, plus a formal **gamer-caught** check,
  all on a **held-out eval seed range**. All three fast rides VALID; `greedy` caught below random.
  +12 tests (**186**); baselines byte-identical. The deeper construct-validity gaps (convergent/
  criterion validity, the discriminant matrix, ablation, structural ladder, item hygiene) stay open —
  see the bullet above and [`12-validity.md`](12-validity.md).
- **2026-06-04** — **Environment + working-directory confinement of untrusted code** resolved as
  **D-048**: the coding harness spawns the candidate subprocess with a minimal allowlisted environment
  (no inherited secrets in `os.environ`) and a throwaway working directory (relative file writes can't
  touch the repo). Baselines byte-identical; +3 tests. Only a **full OS sandbox** (network/abs-path/
  resource confinement) remains open (see above). See [`07-multi-ride.md`](07-multi-ride.md).
- **2026-06-04** — **Documenting the BYO wire protocol** resolved as **D-047**: a language-agnostic
  HTTP/JSON spec ([`09-byo-protocol.md`](09-byo-protocol.md)) for the D-027 server — endpoints,
  message shapes, the poll loop, and the determinism contract — so a third party can implement an
  agent from the doc alone. (Protocol *hardening* for public hosting — auth/TLS/rate limiting — stays
  open under roadmap #5.)
- **2026-05-31** — **Time-bounding + sandboxing untrusted code** (the coding harness's flagged
  limitation) resolved as **D-043**: candidate source runs in an isolated subprocess
  (`sys.executable -I`) under a wall-clock timeout, talking a text-only stdin/stdout protocol (no
  unpickling); a hanging/crashing/malicious candidate fails (score 0) without freezing or
  compromising the ride. Baselines byte-identical. Only a **full OS sandbox** (FS/network/resource
  confinement) remains open (see above). See [`07-multi-ride.md`](07-multi-ride.md).
- **2026-05-31** — **Spectator surface for the diagnostic outputs** resolved as **D-044**:
  `viewer/profiles.html`, a static zero-dependency page rendering the radar (inline-SVG), career
  (trust-collapse), and leaderboard (reward-hacker callout) from the `--json` outputs. Roadmap #4
  down-payment. See [`07-multi-ride.md`](07-multi-ride.md).
- **2026-05-31** — **Cross-ride "career"** resolved as **D-041** (+ leaderboard **D-042**): the first
  cross-ride coupling. Each ride declares an `integrity` signal; **reputation = the product** of them
  and **`career_score = mean_capability × reputation`**, so misconduct anywhere discounts capability
  everywhere. Built on top of the radar (reuses its deterministic skip); a reward-hacker (`greedy`)
  now ranks last, below `random`. Deliberately reverses part of D-008 (logged in D-041). See
  [`07-multi-ride.md`](07-multi-ride.md).
- **2026-05-30** — **HTTP/JSON server** for external BYO agents built as **D-027** (park-hosted,
  agent-polled, stdlib only; reuses the protocol/engine/runlog unchanged). It realises the wire
  connection D-015 deferred from the core build (D-026). Design in
  [`06-v1-architecture.md`](06-v1-architecture.md).
- **2026-05-30** — **Nudge controls** implemented as **D-029**: persona swap / scenario injection,
  flagged off-record and excluded from canonical profiles; run-log schema versioned with an
  `off_record` flag. See [`06-v1-architecture.md`](06-v1-architecture.md).
- **2026-05-29** — Core v1 ride design locked as **D-015–D-021**.
- **2026-05-29** — Implementation choices locked as **D-023–D-026** (stack, scripted cast, deferred
  LLM, core-only build). The three former v1 ride details are now decided:
  - *Preference generation* → seeded additive utilities with anti-correlated weights
    (D-016; see [`06-v1-architecture.md`](06-v1-architecture.md)).
  - *Round cap* → 8 exchanges per side (D-017).
  - *Persona prompts* → replaced by scripted strategies (D-024).
- **2026-05-30** — Static replay viewer built as **D-028**: `viewer/index.html` (single file,
  no build step, no dependencies). Renders suite header, agent profile, per-persona bars,
  match list, and per-match transcript playback with running score. Sample fixture at
  `viewer/sample-run.json`.
- **2026-05-30** — **LLM provider** wiring resolved as **D-030**: a real LLM reference agent
  (`agents/llm.py`) via OpenRouter's OpenAI-compatible API using stdlib only (no SDK, no new
  runtime dep), with graceful heuristic fallback. Registered as the `llm` CLI agent.
- **2026-05-30** — Ride-refinement questions resolved: **D-031** (per-persona reservation floors →
  crisp, non-overlapping per-persona spread) and **D-032** (suite varies scenario shapes 3–5 × 3–5 +
  moderately dispersed weights). See [`06-v1-architecture.md`](06-v1-architecture.md).
- **2026-05-30** — **Radar roll-up** resolved as **D-037**: per-axis **mean** of the normalized
  `[0, 1]` ride scores; an axis with no ride is **absent** (`n/a`), not 0; a ride that can't score an
  agent is **skipped gracefully**. Built in `src/parkbench/radar.py` (stdlib-only ASCII chart +
  `to_dict()`) with a `parkbench radar` CLI subcommand. See [`07-multi-ride.md`](07-multi-ride.md).
- **2026-05-30** — **Identity & versioning of submitted agents** resolved as **D-038**: every agent
  has a stable `identity()` → `AgentIdentity{name, version, config_hash}` (deterministic short hash
  of the agent's defining config), stamped into the run log as a top-level `agent` block; run-log
  `schema_version` bumped 2 → 3 (additive). Makes results attributable and reproducible over time.
  See [`07-multi-ride.md`](07-multi-ride.md) and [`06-v1-architecture.md`](06-v1-architecture.md).
