"""Structured JSON run logs — the input the future replay viewer will render."""

from __future__ import annotations

import json
import time
from pathlib import Path

from .scoring import Profile, Stat
from .suite import Suite


def _stat(s: Stat) -> dict:
    return {"mean": s.mean, "std": s.std, "ci95": s.ci95, "n": s.n}


def _profile_to_dict(profile: Profile) -> dict:
    return {
        "agent": profile.agent_name,
        "efficiency": _stat(profile.efficiency),
        "own_value": _stat(profile.own_value),
        "deal_rate": profile.deal_rate,
        "per_persona": {
            p: {
                "efficiency": _stat(v["efficiency"]),
                "own_value": _stat(v["own_value"]),
                "deal_rate": v["deal_rate"],
            }
            for p, v in profile.per_persona.items()
        },
    }


def write_run(profile: Profile, records: list[dict], suite: Suite, out_root: str = "runs") -> Path:
    ts = time.strftime("%Y%m%d-%H%M%S")
    run_dir = Path(out_root) / f"{ts}__{profile.agent_name}"
    run_dir.mkdir(parents=True, exist_ok=True)
    payload = {
        "suite": {
            "name": suite.name,
            "seed": suite.seed,
            "n_scenarios": suite.n_scenarios,
            "n_issues": suite.n_issues,
            "n_levels": suite.n_levels,
            "round_cap": suite.round_cap,
        },
        "profile": _profile_to_dict(profile),
        "matches": records,
    }
    (run_dir / "run.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return run_dir
