# 02 — Decision Log

**Status:** Living · **Last updated:** 2026-05-30

Append-only log of decisions and their rationale (lightweight ADR style). When a decision is
reversed or superseded, add a **new** entry referencing the old one rather than editing history.

Format: `ID · Date · Decision · Why · Alternatives rejected`.

---

### D-001 · 2026-05-29 · Primary purpose = agent evaluation arena
**Decision:** The project is, first and foremost, a benchmark/eval environment; success means
trusted, rigorous, reproducible scoring.
**Why:** A single clear purpose keeps the design coherent; the founding survey's "be everything"
stance is a non-product.
**Rejected:** spectator entertainment; open agent playground; personal-only research sandbox (these
become *secondary* flavors at most).

### D-002 · 2026-05-29 · The theme-park metaphor = "rides are scored skill tests"
**Decision:** Each attraction is a self-contained, scored capability test; the park is a modular
benchmark suite.
**Why:** Modularity (add/remove/recompose rides) is the metaphor's real strength and the cleanest
fit for an eval product.
**Rejected:** agents-as-visitors-for-fun; agents-run-the-park (tycoon); a pure emergent-society world.

### D-003 · 2026-05-29 · Human role = observe + nudge
**Decision:** Humans watch (dashboards/replays/profiles) and can nudge (coach agents, inject events).
**Why:** Watchability drives mindshare; "nudge" doubles as an adversarial-robustness probe.
**Rejected:** observe-only; operators-only; humans-play-alongside.

### D-004 · 2026-05-29 · Agent source = hybrid (house cast + BYO)
**Decision:** Maintain a house cast and also accept bring-your-own agents over a published protocol.
**Why:** The **house cast becomes the reproducibility mechanism** for multi-agent rides (fixed
counterparties ⇒ stable scores). This is load-bearing, not cosmetic.
**Rejected:** house-cast-only; BYO-only; single-model-many-copies (the last is a future research mode).

### D-005 · 2026-05-29 · Measure all four skill families (full vision)
**Decision:** Social/negotiation/coalitions, Economic/resource, Coding/tool-use, Safety/robustness.
**Why:** They map 1:1 onto the four axes of the diagnostic radar (skills = output spine).
**Note:** This is the destination; v1 measures only one (see D-009).

### D-006 · 2026-05-29 · Ride formats = both solo and multi-agent (full vision)
**Decision:** Some clean solo rides, some multi-agent social rides.
**Why:** Multi-agent is the differentiator; solo gives clean, trusted contrast.
**Rejected:** solo-only (too close to existing benchmarks); multi-agent-only (harder to bootstrap trust).

### D-007 · 2026-05-29 · Headline output = diagnostic skill profile (radar)
**Decision:** Output is a per-skill, per-ride diagnostic profile, not a single rank or pass/fail.
**Why:** Most useful for *improving* an agent; aligns with the four-skill spine.
**Rejected:** leaderboard/ranking (a possible later add); certification; story-log-only.

### D-008 · 2026-05-29 · Park structure = independent rides in v1, connected later
**Decision:** Rides are scored in isolation now; cross-ride reputation/resource coupling comes later.
**Why:** Clean, reproducible scoring first; emergent "career" richness once the basics are trusted.
**Rejected:** independent-forever; connected-career-from-day-one (too messy to score early).

### D-009 · 2026-05-29 · v1 = "hard part first" — one flagship multi-agent social ride
**Decision:** Build exactly one ride first: a multi-agent social ride, scored reproducibly via the
house cast.
**Why:** Prove the hardest, most differentiating capability (reproducible social scoring) before
investing in breadth.
**Rejected:** vertical-slice across formats; breadth (one shallow ride per axis); depth on several
social rides.

### D-010 · 2026-05-29 · Flagship ride = multi-issue negotiation
**Decision:** The first ride is multi-issue negotiation between the test agent and the house cast.
**Why:** Objective payoff, low variance, fixed counterparties — best proves *reproducible
multi-agent social scoring*, which is exactly what v1 exists to demonstrate.
**Rejected:** social deduction (most watchable but noisy ⇒ undercuts the goal); coalition formation
(more complex rules); commons/public-goods (good, kept as a sibling candidate).

### D-011 · 2026-05-29 · Scoring = objective payoff vs. baselines
**Decision:** Score = value captured / goal achieved, normalized against reference agents.
**Why:** Rigorous, reproducible, hard to game — the trustworthy backbone v1 needs.
**Rejected:** judge-LLM rubric (bias/gameable); peer ratings (circular); blend (deferred until
qualitative axes are needed).

### D-012 · 2026-05-29 · Theming = mechanics first, theme later
**Decision:** Build the eval engine and scoring; apply the creative skin afterward.
**Why:** Theming is a thin layer over correct mechanics; spectacle has no value if the scores aren't.
**Rejected:** theme-core-from-day-one; light-theme-now.

### D-013 · 2026-05-29 · Commercial model = deferred (open/free for now)
**Decision:** No monetization in the near term; optimize for adoption, mindshare, and learning.
**Why:** Trust and usage must precede any business model for a benchmark.
**Rejected:** eval-as-a-service; public leaderboard + sponsorship; spectator/media product (all
revisited post-adoption).

### D-014 · 2026-05-29 · Documentation-first working model
**Decision:** Everything is heavily documented for both the agent and the human owner; `docs/` is the
source of truth; agents must read `CLAUDE.md` + `docs/` before working and keep them in sync.
**Why:** Owner requirement; the doc set will grow incrementally and must stay authoritative.
**Rejected:** lightweight/ad-hoc documentation.

### D-015 · 2026-05-29 · BYO connection = HTTP/JSON, park-orchestrated
**Decision:** External agents connect over a plain HTTP/JSON request-response API; the park drives
the loop (sends a JSON observation on the agent's turn, receives a JSON action).
**Why:** Universal — any agent framework can call it — and trivial to test; the park staying in
control keeps runs deterministic.
**Rejected:** WebSocket/real-time (unneeded for turn-based v1); MCP (revisit later as an ergonomic wrapper).

### D-016 · 2026-05-29 · Negotiation = integrative, multi-issue, private preferences
**Decision:** 3–5 issues, asymmetric preference weights, each agent knows only its own preferences
(information asymmetry on).
**Why:** Integrative structure forces agents to *discover* value-creating trades — the thing that
separates a real negotiator from a naive one — and yields a clean "% of achievable joint value
captured" measure. Pure distributive (zero-sum split) would mostly measure aggression.
**Rejected:** distributive/single-pie; full information.

### D-017 · 2026-05-29 · Interaction = turn-based, capped, text + structured offer
**Decision:** Turn-based with a round cap (or deadline). Each turn allows a **free-text message** and
a **structured offer/accept** action.
**Why:** Free text captures real negotiation behavior; the structured offer is machine-parseable so
scoring reflects what was actually agreed, not an interpretation of prose.
**Rejected:** free-text-only (ambiguous to score); structured-only (loses the social signal).

### D-018 · 2026-05-29 · House cast = bilateral, 3–4 fixed personas, deterministic
**Decision:** Bilateral negotiations (one counterpart per run) drawn from a roster of 3–4 fixed
personas (e.g., tough / fair / cooperative / slippery), run at temperature 0 or a fixed seed with
frozen persona prompts. The test agent faces each persona.
**Why:** Determinism is what makes scores reproducible; a small persona roster also reveals *who* an
agent struggles against.
**Rejected:** multilateral in v1; single counterpart only; nondeterministic cast.

### D-019 · 2026-05-29 · Baselines = optimum + floor; report two numbers
**Decision:** Anchor scores to the game-theoretic optimum (Pareto frontier / Nash bargaining
solution) as the ceiling and a weak agent (random/greedy) as the floor. Report **joint value
captured** and **own share** separately.
**Why:** The optimum is an absolute, gaming-resistant reference; the two numbers distinguish "found
the trades at all" from "captured value for itself / avoided being exploited."
**Rejected:** single composite score; LLM-judged scoring.

### D-020 · 2026-05-29 · A "score" = fixed suite of ~10–20 scenarios, mean + variance
**Decision:** Score an agent over a fixed suite of ~10–20 negotiation scenarios (varying issue
weights/structure), reporting the mean with a variance / confidence interval.
**Why:** Enough scenarios to discriminate and to *measure* reproducibility (the variance is the
evidence for the v1 claim); small enough to rerun cheaply.
**Rejected:** single-scenario scoring; very large suites (too slow/expensive for v1).

### D-021 · 2026-05-29 · Observe+nudge surface (v1) = logs + replay; nudges flagged off-record
**Decision:** v1 surface is structured run logs plus a simple replay viewer (transcript playback +
running score). "Nudge" = inject a chosen scenario or swap the counterpart persona; nudged runs are
flagged **off-record** and excluded from canonical profiles.
**Why:** Minimal surface proves the observe+nudge loop without building a full dashboard; flagging
protects score integrity.
**Rejected:** full live dashboard in v1; allowing nudged runs into canonical scores.

### D-022 · 2026-05-29 · Project name = "Parkbench"; public repo
**Decision:** The project and GitHub repo are named **Parkbench** ("park" + "benchmark"; also a real
object — a bench in a park). Repo: `github.com/aravmdn/parkbench`, **public**.
**Why:** A memorable identity aids the long-term mindshare goal, and the repo needs a name now.
Naming is identity, not lore, so it doesn't conflict with "mechanics first, theme later" (D-012).
Public matches the open/free ethos (D-013).
**Rejected:** descriptive slug (`theme-park-for-ai-agents`); Midway; Arcade; Funhouse; private visibility.

### D-023 · 2026-05-29 · Stack = Python 3.11+, `src/` layout
**Decision:** Implement the engine, scenarios, scoring, agents, and CLI in Python 3.11+ with a `src/`
layout and zero runtime dependencies. The replay viewer (later) will be static HTML/JS over the JSON
run logs.
**Why:** Best ecosystem for eval/LLM/data work; zero deps keeps install/run trivial.
**Rejected:** Python + FastAPI web app (more than v1 needs); TypeScript/Node full-stack.

### D-024 · 2026-05-29 · House cast = scripted deterministic personas (refines D-018)
**Decision:** The four house personas (tough / fair / cooperative / slippery) are scripted
deterministic strategies (a shared time-based concession + logrolling strategy), **not** temp-0 LLMs.
**Why:** Determinism removes the largest source of score variance — exactly the reproducibility v1
exists to prove. This **refines D-018**, which had assumed temp-0 LLM personas; LLM personas become
a fast-follow.
**Rejected:** LLM personas at temp 0; hybrid scripted+LLM.

### D-025 · 2026-05-29 · LLM provider deferred; ship a stubbed provider-agnostic seam
**Decision:** Ship a `Provider` interface + `LLMAgent` stub; v1 validation uses non-LLM agents
(random, greedy, heuristic). No provider/key is wired yet.
**Why:** A real LLM isn't needed to prove reproducibility + discrimination, and staying
provider-agnostic keeps BYO open.
**Rejected:** committing to Anthropic or OpenAI now.

### D-026 · 2026-05-29 · This build = core only (engine + scoring + CLI)
**Decision:** Build the engine, seeded scenario generator, scoring, scripted cast, baseline/heuristic
agents, JSON run logs, and a CLI. Defer the HTTP server, replay viewer, nudge, and LLM reference agent.
**Why:** Prove the hard part (a trustworthy, reproducible social score) on the smallest runnable slice.
**Validation:** 14 passing tests incl. a determinism check; the CLI shows clean separation
(efficiency: heuristic 0.978 > random 0.840 > greedy 0.412) with tight CIs and exact reproducibility.
Full design + formulas in [`06-v1-architecture.md`](06-v1-architecture.md).

### D-030 · 2026-05-30 · LLM reference agent = OpenRouter via stdlib (refines/closes D-025)
**Decision:** Implement the deferred LLM reference agent in `agents/llm.py`: a `Provider` seam
(`complete(messages, **opts) -> str`) plus a concrete `OpenRouterProvider` that POSTs to OpenRouter's
OpenAI-compatible endpoint (`https://openrouter.ai/api/v1/chat/completions`) using **only stdlib**
`urllib.request` + `json` — **no third-party SDK, no new runtime dependency** (honours D-023). The
key comes from `OPENROUTER_API_KEY`; the model from `OPENROUTER_MODEL`, defaulting to a free
(`:free`) model id held in the `DEFAULT_MODEL` constant. `LLMAgent.act` builds a compact prompt from
**only the agent's own** utilities (private preferences, D-016) + standing offer + rounds-left +
recent history, requires a single strict JSON action, parses/validates it into a `protocol.Action`,
and **degrades gracefully** to the `HeuristicNegotiator` move on any missing-key/network/parse/
validation error (no stdout, short HTTP timeout) so a run never crashes or hangs. Registered as the
`llm` agent in the CLI; runnable with or without a key.
**Why:** A real reference agent is now useful, and OpenRouter's OpenAI-compatible API gives free
models behind one key while staying provider-agnostic (BYO stays open). Stdlib-only keeps the
zero-dep promise. This **refines and closes D-025** (which shipped only the stub seam).
**Rejected:** committing to a vendor SDK (`openai`/`anthropic`) or any new runtime dependency;
hard-failing when no key is set (would make `llm` unrunnable in CI / offline).
