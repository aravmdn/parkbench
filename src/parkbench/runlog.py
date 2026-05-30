"""Structured JSON run logs — the input the future replay viewer will render."""

from __future__ import annotations

import json
import time
from pathlib import Path

from .agents.base import Agent, AgentIdentity
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


def _identity_block(profile: Profile, agent: Agent | None) -> dict:
    """The top-level `agent` identity block (decision D-038).

    When an `Agent` is supplied its `identity()` is used directly. Otherwise (callers that
    don't have the agent object) the block is derived from the profile's agent name with a
    sensible default version + configless hash, so the field is always present and stable.
    """
    if agent is not None:
        return agent.identity().to_dict()
    from .agents.base import config_hash

    return AgentIdentity(
        name=profile.agent_name,
        version="0",
        config_hash=config_hash({}),
    ).to_dict()


# Run-log schema version. Bumped to 3 with D-038, which ADDED the top-level `agent` identity
# block {name, version, config_hash}. D-029 bumped it to 2 (added `schema_version` and the
# top-level `off_record` flag). v1 logs (no version key) are treated as schema_version 1.
# All bumps are additive: existing fields keep their names and positions.
SCHEMA_VERSION = 3


def write_run(
    profile: Profile,
    records: list[dict],
    suite: Suite,
    out_root: str = "runs",
    off_record: bool | None = None,
    agent: Agent | None = None,
) -> Path:
    """Write a JSON run log.

    `off_record` flags a nudged run (D-029); when omitted it is inferred from the profile so
    callers that don't know about nudging still log correctly.

    `agent`, when supplied, stamps that agent's stable `identity()` into the top-level
    `agent` block (D-038); when omitted the block is derived from the profile's agent name
    with a default version, so the field is always present and the call stays backward
    compatible.
    """
    if off_record is None:
        off_record = bool(getattr(profile, "off_record", False))
    ts = time.strftime("%Y%m%d-%H%M%S")
    suffix = "__off_record" if off_record else ""
    run_dir = Path(out_root) / f"{ts}__{profile.agent_name}{suffix}"
    run_dir.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema_version": SCHEMA_VERSION,
        "off_record": off_record,
        "agent": _identity_block(profile, agent),
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
