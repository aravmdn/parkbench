"""Parkbench command-line interface.

  parkbench run     — run an agent through the negotiation suite and print its profile.
  parkbench analyze — print a single scenario's optimum (for debugging / inspection).
"""

from __future__ import annotations

import argparse
import sys

from .agents import AGENT_REGISTRY, make_agent
from .agents.baselines import RandomAgent
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
    profile, records = run_suite(suite, make_agent(args.agent), nudge)
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
        run_dir = write_run(profile, records, suite, off_record=nudge.off_record)
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
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    args.func(args)
    return 0


if __name__ == "__main__":
    sys.exit(main())
