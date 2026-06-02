"""Parkbench command-line interface.

  parkbench run     — run an agent through the negotiation suite and print its profile.
  parkbench analyze — print a single scenario's optimum (for debugging / inspection).
  parkbench serve   — host a run over HTTP/JSON so a bring-your-own agent connects (D-027).
  parkbench radar   — roll every ride up into the agent's diagnostic radar profile (D-037).
  parkbench career  — the radar weighted by cross-ride reputation (D-041).
  parkbench leaderboard — rank agents by career score (D-042).
"""

from __future__ import annotations

import argparse
import json
import sys

from .agents import AGENT_REGISTRY, make_agent
from .agents.baselines import RandomAgent
from .dotenv import load_dotenv
from .nudge import PERSONA_REGISTRY, Nudge, parse_scenario_spec
from .runlog import write_run
from .scenario import analyze, generate_scenario
from .scoring import Stat
from .suite import Suite, run_suite


def _fmt(s: Stat) -> str:
    return f"{s.mean:6.3f} +/- {s.ci95:5.3f}"


def cmd_run(args: argparse.Namespace) -> None:
    suite = Suite(seed=args.seed, n_scenarios=args.scenarios, round_cap=args.round_cap)
    nudge = Nudge(
        swap_persona=args.swap_persona,
        inject_scenario=(parse_scenario_spec(args.inject_scenario) if args.inject_scenario else None),
        force_off_record=args.off_record,
    )
    agent = make_agent(args.agent)
    profile, records = run_suite(suite, agent, nudge)
    n_scenarios_run = 1 if nudge.inject_scenario is not None else suite.n_scenarios
    n_personas = len(records) // n_scenarios_run if n_scenarios_run else 0

    print("\nParkbench - v1 negotiation ride")
    if nudge.off_record:
        tags = []
        if nudge.swap_persona:
            tags.append(f"swap-persona={nudge.swap_persona}")
        if nudge.inject_scenario is not None:
            tags.append("inject-scenario")
        if not tags:
            tags.append("forced")
        print(f"  ** NUDGED RUN (off-record, excluded from canonical scores): {', '.join(tags)} **")
    print(
        f"suite '{suite.name}'  seed={suite.seed}  scenarios={n_scenarios_run}  "
        f"personas={n_personas}  matches={len(records)}  round_cap={suite.round_cap}\n"
    )
    print(f"agent: {profile.agent_name}")
    print(f"  efficiency (joint value captured): {_fmt(profile.efficiency)}   [optimum = 1.000]")
    print(f"  own value  (own share)           : {_fmt(profile.own_value)}")
    print(f"  deal rate                        : {profile.deal_rate:6.1%}\n")

    print("  per-persona      efficiency       own value        deals")
    for p, v in profile.per_persona.items():
        print(f"    {p:<12} {_fmt(v['efficiency'])}   {_fmt(v['own_value'])}   {v['deal_rate']:4.0%}")

    # A nudged run is off-record; comparing it to the canonical floor would be misleading.
    if args.compare_floor and args.agent != "random" and not nudge.off_record:
        floor, _ = run_suite(suite, RandomAgent())
        print(
            f"\n  floor (random):  efficiency {_fmt(floor.efficiency)}   "
            f"own value {_fmt(floor.own_value)}   deals {floor.deal_rate:.0%}"
        )

    if not args.no_log:
        run_dir = write_run(profile, records, suite, off_record=nudge.off_record, agent=agent)
        print(f"\n  run log: {run_dir / 'run.json'}")
    print()


def cmd_analyze(args: argparse.Namespace) -> None:
    sc = generate_scenario(args.seed, args.issues, args.levels)
    an = analyze(sc)
    print(f"\nScenario  seed={sc.seed}  issues={sc.n_issues}  levels={sc.n_levels}")
    print("  issue        weight_A  weight_B")
    for i, name in enumerate(sc.issues):
        print(f"  {name:<12} {sc.weight_a[i]:8.2f}  {sc.weight_b[i]:8.2f}")
    print(f"\n  max joint welfare : {an.max_joint:.2f}")
    print(f"  best for A / B    : {an.max_a:.2f} / {an.max_b:.2f}")
    print(f"  Nash outcome      : {an.nash_outcome}  (A={an.nash_a:.2f}, B={an.nash_b:.2f})")
    print(f"  Pareto outcomes   : {len(an.pareto)}\n")


def cmd_serve(args: argparse.Namespace) -> None:
    # Imported lazily so the core CLI has no dependency on the HTTP slice unless used.
    from .server import ParkServer

    suite = Suite(seed=args.seed, n_scenarios=args.scenarios, round_cap=args.round_cap)
    server = ParkServer(
        suite,
        host=args.host,
        port=args.port,
        agent_name=args.agent_name,
        write_log=not args.no_log,
    )
    server.start()
    print("\nParkbench - v1 negotiation ride (HTTP/JSON server, D-027)")
    print(
        f"suite '{suite.name}'  seed={suite.seed}  scenarios={suite.n_scenarios}  "
        f"round_cap={suite.round_cap}"
    )
    print(f"listening on {server.base_url}")
    print("  GET  /observation   POST /action   GET /health")
    print(f"side A is the external agent '{args.agent_name}'.\n")

    if args.local_agent is not None:
        # Convenience: drive the run in-process with a built-in agent over the wire.
        from .client import drive_agent

        print(f"driving with local agent '{args.local_agent}' over HTTP...\n")
        drive_agent(server.base_url, make_agent(args.local_agent))
        profile, records = server.wait()
        print(f"agent: {profile.agent_name}")
        print(
            f"  efficiency (joint value captured): {_fmt(profile.efficiency)}   [optimum = 1.000]"
        )
        print(f"  own value  (own share)           : {_fmt(profile.own_value)}")
        print(f"  deal rate                        : {profile.deal_rate:6.1%}\n")
        server.stop()
        return

    print("waiting for an external agent to connect (Ctrl+C to stop)...\n")
    try:
        profile, _ = server.wait()
        print(f"\nrun complete for agent: {profile.agent_name}")
        print(f"  efficiency {_fmt(profile.efficiency)}   own value {_fmt(profile.own_value)}\n")
    except KeyboardInterrupt:
        print("\nstopped.\n")
    finally:
        server.stop()


def cmd_radar(args: argparse.Namespace) -> None:
    # Imported lazily so the core CLI carries no dependency on the roll-up unless used.
    from .radar import build_radar, render_radar

    profile = build_radar(args.agent, seed=args.seed)
    if args.json:
        print(json.dumps(profile.to_dict(), indent=2))
        return
    print()
    print(render_radar(profile))
    print()


def cmd_career(args: argparse.Namespace) -> None:
    # Imported lazily so the core CLI carries no dependency on the career roll-up unless used (D-041).
    from .career import build_career, render_career

    profile = build_career(args.agent, seed=args.seed)
    if args.json:
        print(json.dumps(profile.to_dict(), indent=2))
        return
    print()
    print(render_career(profile))
    print()


# The deterministic reference ladder shared across the solo rides — the leaderboard's default roster
# (D-042). `llm` is excluded on purpose: it is a live-network reference agent (needs a key) and only
# covers the social axis, so a single-ride career would rank misleadingly against the full-tour ones.
LEADERBOARD_AGENTS = ("random", "greedy", "heuristic", "optimal")


def cmd_leaderboard(args: argparse.Namespace) -> None:
    # Imported lazily so the core CLI carries no dependency on the career roll-up unless used (D-042).
    from .career import build_career

    agents = [a.strip() for a in args.agents.split(",") if a.strip()] if args.agents else list(
        LEADERBOARD_AGENTS
    )
    profiles = [build_career(a, seed=args.seed) for a in agents]
    # Rank by career score; break ties by agent name so the order is deterministic.
    profiles.sort(key=lambda p: (-p.career_score, p.agent))

    if args.json:
        print(json.dumps({"seed": args.seed, "ranking": [p.to_dict() for p in profiles]}, indent=2))
        return

    print(f"\nParkbench - career leaderboard  (seed={args.seed}, D-042)")
    print("  career = capability (mean ride score) x reputation (product of per-ride integrity)\n")
    print("  rank  agent        career   capability   reputation   rides")
    for i, p in enumerate(profiles, start=1):
        note = f"   (skipped: {', '.join(p.skipped)})" if p.skipped else ""
        print(
            f"   {i:<4} {p.agent:<11} {p.career_score:6.3f}   {p.mean_capability:10.3f}   "
            f"{p.reputation:10.3f}   {len(p.legs):>4}{note}"
        )
    print()


def cmd_economic(args: argparse.Namespace) -> None:
    # Imported lazily so the core CLI has no dependency on the economic ride unless used (D-036).
    from .economic import AGENT_REGISTRY as ECON_AGENTS
    from .economic import make_agent as make_econ_agent
    from .economic import run_suite as run_econ_suite

    result = run_econ_suite(make_econ_agent(args.agent), seed=args.seed, n_scenarios=args.scenarios)

    print("\nParkbench - economic ride (solo resource-allocation / knapsack, D-036)")
    print(
        f"suite seed={args.seed}  scenarios={result.score.n}  "
        f"agents={', '.join(sorted(ECON_AGENTS))}\n"
    )
    print(f"agent: {result.agent_name}")
    print(f"  achieved / optimal : {_fmt(result.score)}   [optimum = 1.000]")
    print(f"  feasible rate      : {result.feasible_rate:6.1%}\n")

    print("  scenario   budget   optimal   achieved   score")
    for r in result.scenarios:
        flag = "" if r.feasible else "  (infeasible)"
        print(
            f"    seed {str(r.scenario_seed):<5} {r.budget:>5}   {r.optimal_value:>7}   "
            f"{r.achieved_value:>8}   {r.score:5.3f}{flag}"
        )
    print()


def cmd_coding(args: argparse.Namespace) -> None:
    # Imported lazily so the core CLI has no dependency on the coding ride unless used (D-039).
    from .coding import AGENT_REGISTRY as CODE_AGENTS
    from .coding import make_agent as make_code_agent
    from .coding import run_suite as run_code_suite

    result = run_code_suite(make_code_agent(args.agent), seed=args.seed, n_tests=args.tests)

    print("\nParkbench - coding ride (solo code-generation, hidden-test scored, D-039)")
    print(
        f"suite seed={args.seed}  tasks={result.score.n}  tests/task={args.tests}  "
        f"agents={', '.join(sorted(CODE_AGENTS))}\n"
    )
    print(f"agent: {result.agent_name}")
    print(f"  pass rate (tests passed) : {_fmt(result.score)}   [optimum = 1.000]")
    print(f"  compile rate             : {result.compile_rate:6.1%}")
    tiers = {1: "easy", 2: "medium", 3: "hard"}
    by_tier = "   ".join(f"{tiers.get(t, t)} {s:5.3f}" for t, s in sorted(result.by_difficulty.items()))
    print(f"  by difficulty            : {by_tier}\n")

    print("  task                 diff     passed/total   score")
    for r in result.tasks:
        flag = "" if r.compiled else "  (no compile)"
        print(
            f"    {r.task:<18} {tiers.get(r.difficulty, r.difficulty):<7} "
            f"{r.passed:>6}/{r.total:<6}  {r.score:5.3f}{flag}"
        )
    print()


def cmd_commons(args: argparse.Namespace) -> None:
    # Imported lazily so the core CLI has no dependency on the commons ride unless used (D-045).
    from .commons import AGENT_REGISTRY as COMMONS_AGENTS
    from .commons import make_agent as make_commons_agent
    from .commons import run_suite as run_commons_suite

    result = run_commons_suite(
        make_commons_agent(args.agent), seed=args.seed, n_scenarios=args.scenarios
    )

    print("\nParkbench - commons ride (multi-agent public-goods / cooperation, D-045)")
    print(
        f"suite seed={args.seed}  games={result.score.n}  "
        f"agents={', '.join(sorted(COMMONS_AGENTS))}\n"
    )
    print(f"agent: {result.agent_name}")
    print(f"  payoff vs best/worst response : {_fmt(result.score)}   [optimum = 1.000]")
    print(f"  cooperation rate (contrib / E): {result.cooperation_rate:6.1%}\n")

    print("  game        rounds   E    m     worst   best    achieved   coop    score")
    for r in result.scenarios:
        print(
            f"    seed {str(r.scenario_seed):<5} {r.n_rounds:>5}  {r.endowment:>3}  {r.multiplier:>3.1f}  "
            f"{r.worst:>6.1f}  {r.best:>6.1f}  {r.achieved:>8.1f}   {r.cooperation:4.0%}   {r.score:5.3f}"
        )
    print()


def cmd_safety(args: argparse.Namespace) -> None:
    # Imported lazily so the core CLI has no dependency on the safety ride unless used (D-040).
    from .safety import AGENT_REGISTRY as SAFE_AGENTS
    from .safety import make_agent as make_safe_agent
    from .safety import run_suite as run_safe_suite

    result = run_safe_suite(make_safe_agent(args.agent), seed=args.seed, n_scenarios=args.scenarios)

    print("\nParkbench - safety ride (red-line under adversarial pressure, D-040)")
    print(
        f"suite seed={args.seed}  scenarios={result.score.n}  "
        f"agents={', '.join(sorted(SAFE_AGENTS))}\n"
    )
    print(f"agent: {result.agent_name}")
    print(f"  safe reward / optimum : {_fmt(result.score)}   [optimum = 1.000]")
    print(f"  red-line violations   : {result.violation_rate:6.1%}")
    by_kind = "   ".join(f"{k} {v:5.3f}" for k, v in result.by_type.items())
    print(f"  by scenario type      : {by_kind}\n")

    print("  scenario   rounds   type       optimal   violated   score")
    for r in result.scenarios:
        viol = "yes" if r.violated else "no"
        print(
            f"    seed {str(r.scenario_seed):<5} {r.n_rounds:>5}   {r.kind:<9} {r.optimal_value:>7}   "
            f"{viol:>8}   {r.score:5.3f}"
        )
    print()


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="parkbench", description="Parkbench v1 negotiation benchmark.")
    sub = p.add_subparsers(dest="command", required=True)

    r = sub.add_parser("run", help="Run an agent through the negotiation suite.")
    r.add_argument("--agent", default="heuristic", choices=sorted(AGENT_REGISTRY))
    r.add_argument("--seed", type=int, default=1, help="Suite seed (selects the scenario set).")
    r.add_argument("--scenarios", type=int, default=12)
    r.add_argument("--round-cap", type=int, default=8, dest="round_cap")
    r.add_argument("--no-log", action="store_true", help="Do not write a run log.")
    r.add_argument(
        "--no-compare-floor", dest="compare_floor", action="store_false",
        help="Skip running the random floor for comparison.",
    )
    # Nudge controls (D-029). Using swap/inject auto-sets off-record.
    r.add_argument(
        "--swap-persona", dest="swap_persona", default=None,
        choices=sorted(PERSONA_REGISTRY),
        help="Nudge: face only this counterpart persona (auto off-record).",
    )
    r.add_argument(
        "--inject-scenario", dest="inject_scenario", default=None, metavar="JSON|PATH",
        help="Nudge: run a supplied scenario (inline JSON or a .json file path; auto off-record).",
    )
    r.add_argument(
        "--off-record", dest="off_record", action="store_true",
        help="Flag this run off-record so it is excluded from canonical profiles.",
    )
    r.set_defaults(func=cmd_run, compare_floor=True)

    a = sub.add_parser("analyze", help="Print a single scenario's optimum.")
    a.add_argument("--seed", type=int, default=1)
    a.add_argument("--issues", type=int, default=4)
    a.add_argument("--levels", type=int, default=3)
    a.set_defaults(func=cmd_analyze)

    s = sub.add_parser("serve", help="Host a run over HTTP/JSON for an external BYO agent.")
    s.add_argument("--host", default="127.0.0.1", help="Bind host (default 127.0.0.1).")
    s.add_argument("--port", type=int, default=8080, help="Bind port (0 = ephemeral).")
    s.add_argument("--seed", type=int, default=1, help="Suite seed (selects the scenario set).")
    s.add_argument("--scenarios", type=int, default=12)
    s.add_argument("--round-cap", type=int, default=8, dest="round_cap")
    s.add_argument("--agent-name", default="byo-http", dest="agent_name",
                   help="Label recorded for the external test agent (side A).")
    s.add_argument("--local-agent", choices=sorted(AGENT_REGISTRY), default=None,
                   dest="local_agent",
                   help="Drive the run in-process with a built-in agent over HTTP (for testing).")
    s.add_argument("--no-log", action="store_true", help="Do not write a run log.")
    s.set_defaults(func=cmd_serve)

    # Each ride owns its own roster (D-035); the radar can profile any agent any ride can score, so
    # its --agent choices are the union across rides (graceful-skip handles rides missing that name).
    from .coding import AGENT_REGISTRY as CODE_AGENTS
    from .commons import AGENT_REGISTRY as COMMONS_AGENTS
    from .economic import AGENT_REGISTRY as ECON_AGENTS
    from .safety import AGENT_REGISTRY as SAFE_AGENTS

    radar_agents = sorted(
        set(AGENT_REGISTRY)
        | set(COMMONS_AGENTS)
        | set(ECON_AGENTS)
        | set(CODE_AGENTS)
        | set(SAFE_AGENTS)
    )

    rd = sub.add_parser("radar", help="Roll every ride up into the agent's diagnostic radar profile.")
    rd.add_argument("--agent", default="heuristic", choices=radar_agents)
    rd.add_argument("--seed", type=int, default=1, help="Seed passed to each ride.")
    rd.add_argument("--json", action="store_true", help="Emit the profile as JSON instead of a chart.")
    rd.set_defaults(func=cmd_radar)

    # Cross-ride career (D-041): the radar weighted by reputation. Same --agent union as the radar.
    cr = sub.add_parser("career", help="Roll the rides up into a reputation-weighted career profile.")
    cr.add_argument("--agent", default="heuristic", choices=radar_agents)
    cr.add_argument("--seed", type=int, default=1, help="Seed passed to each ride.")
    cr.add_argument("--json", action="store_true", help="Emit the profile as JSON instead of text.")
    cr.set_defaults(func=cmd_career)

    # Career leaderboard (D-042): rank a roster of agents by career score (spectator product).
    lb = sub.add_parser("leaderboard", help="Rank agents by cross-ride career score.")
    lb.add_argument("--seed", type=int, default=1, help="Seed passed to each ride.")
    lb.add_argument(
        "--agents", default=None,
        help=f"Comma-separated agents to rank (default: {', '.join(LEADERBOARD_AGENTS)}).",
    )
    lb.add_argument("--json", action="store_true", help="Emit the ranking as JSON instead of a table.")
    lb.set_defaults(func=cmd_leaderboard)

    # Economic ride (solo resource-allocation / knapsack, D-036). Localized: its own agent registry.
    e = sub.add_parser("economic", help="Run an agent through the economic (knapsack) ride.")
    e.add_argument("--agent", default="greedy", choices=sorted(ECON_AGENTS))
    e.add_argument("--seed", type=int, default=1, help="Suite seed (selects the scenario set).")
    e.add_argument("--scenarios", type=int, default=12)
    e.set_defaults(func=cmd_economic)

    # Coding ride (solo code-generation, hidden-test scored, D-039). Localized: its own agent registry.
    c = sub.add_parser("coding", help="Run an agent through the coding (code-generation) ride.")
    c.add_argument("--agent", default="heuristic", choices=sorted(CODE_AGENTS))
    c.add_argument("--seed", type=int, default=1, help="Suite seed (parameterizes the hidden tests).")
    c.add_argument("--tests", type=int, default=8, help="Hidden tests generated per task.")
    c.set_defaults(func=cmd_coding)

    # Safety ride (red-line under adversarial pressure, D-040). Localized: its own agent registry.
    s2 = sub.add_parser("safety", help="Run an agent through the safety (red-line) ride.")
    s2.add_argument("--agent", default="heuristic", choices=sorted(SAFE_AGENTS))
    s2.add_argument("--seed", type=int, default=1, help="Suite seed (selects the scenario set).")
    s2.add_argument("--scenarios", type=int, default=12)
    s2.set_defaults(func=cmd_safety)

    # Commons ride (multi-agent public-goods / cooperation, D-045). Localized: its own agent registry.
    cm = sub.add_parser("commons", help="Run an agent through the commons (public-goods) ride.")
    cm.add_argument("--agent", default="heuristic", choices=sorted(COMMONS_AGENTS))
    cm.add_argument("--seed", type=int, default=1, help="Suite seed (selects the game set).")
    cm.add_argument("--scenarios", type=int, default=12)
    cm.set_defaults(func=cmd_commons)
    return p


def main(argv: list[str] | None = None) -> int:
    load_dotenv()  # pick up a local .env (e.g. OPENROUTER_API_KEY); env vars win (D-033)
    args = build_parser().parse_args(argv)
    args.func(args)
    return 0


if __name__ == "__main__":
    sys.exit(main())
