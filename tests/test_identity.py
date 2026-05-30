"""Agent identity & versioning (decision D-038).

Covers: identity is stable/deterministic across instances and processes, differs when an
agent's config differs, appears correctly in the written run.json, and the existing run-log
fields (and their positions) remain intact under the schema_version bump.
"""

from __future__ import annotations

import json

from parkbench import __version__
from parkbench.agents import make_agent
from parkbench.agents.base import Agent, AgentIdentity, config_hash
from parkbench.agents.conceder import ConcederStrategy
from parkbench.runlog import SCHEMA_VERSION, write_run
from parkbench.suite import Suite, run_suite


# --- determinism / stability ------------------------------------------------------------

def test_identity_is_deterministic_across_instances():
    a = make_agent("heuristic").identity()
    b = make_agent("heuristic").identity()
    assert a == b
    assert isinstance(a, AgentIdentity)


def test_config_hash_is_stable_and_independent_of_memory():
    # Same config -> same hash, recomputed fresh each time (no object identity / addresses).
    assert config_hash({"start": 0.85, "end": 0.4}) == config_hash({"start": 0.85, "end": 0.4})
    # Key order does not matter (canonical encoding).
    assert config_hash({"a": 1, "b": 2}) == config_hash({"b": 2, "a": 1})
    # None and {} hash identically (configless agents get a stable identity).
    assert config_hash(None) == config_hash({})


def test_config_hash_is_short_and_hex():
    h = config_hash({"x": 1})
    assert len(h) == 12
    int(h, 16)  # raises if not hex


# --- differs when config differs --------------------------------------------------------

def test_identity_differs_when_config_differs():
    a = ConcederStrategy(name="x", start=0.85, end=0.40, noise=0.0).identity()
    b = ConcederStrategy(name="x", start=0.50, end=0.40, noise=0.0).identity()
    assert a.name == b.name
    assert a.config_hash != b.config_hash  # different concession schedule -> different identity


def test_parameterless_agent_has_empty_config_hash():
    # greedy declares no config, so it hashes to the canonical empty-config hash.
    assert make_agent("greedy").identity().config_hash == config_hash({})


def test_distinct_agents_have_distinct_names():
    assert make_agent("greedy").identity().name == "greedy"
    assert make_agent("heuristic").identity().name == "heuristic"


# --- default version --------------------------------------------------------------------

def test_version_defaults_to_package_version():
    assert make_agent("heuristic").identity().version == __version__


def test_version_falls_back_to_zero_when_blank():
    class _NoVersion(Agent):
        name = "noversion"
        version = ""  # blank -> fall back to package version or "0"

        def act(self, obs):  # pragma: no cover - never called
            raise NotImplementedError

    ident = _NoVersion().identity()
    # Falls back to the package version (non-empty); if that were empty it would be "0".
    assert ident.version


# --- backward compatibility -------------------------------------------------------------

def test_existing_agents_construct_and_identify_unchanged():
    for name in ("random", "greedy", "heuristic", "llm"):
        ident = make_agent(name).identity()
        assert ident.name == name
        assert ident.version
        assert ident.config_hash


# --- run-log stamping (D-038) -----------------------------------------------------------

def test_runlog_stamps_agent_identity(tmp_path):
    suite = Suite(seed=1, n_scenarios=2)
    agent = make_agent("heuristic")
    profile, records = run_suite(suite, agent)
    run_dir = write_run(profile, records, suite, out_root=str(tmp_path), agent=agent)
    payload = json.loads((run_dir / "run.json").read_text(encoding="utf-8"))

    assert payload["schema_version"] == SCHEMA_VERSION == 3
    assert payload["agent"] == agent.identity().to_dict()
    assert set(payload["agent"]) == {"name", "version", "config_hash"}
    assert payload["agent"]["name"] == "heuristic"
    assert payload["agent"]["version"] == __version__
    assert payload["agent"]["config_hash"] == agent.identity().config_hash


def test_runlog_agent_block_present_without_agent_arg(tmp_path):
    # Backward compatible: omitting `agent` still yields a present, well-formed block
    # derived from the profile's agent name.
    suite = Suite(seed=1, n_scenarios=2)
    profile, records = run_suite(suite, make_agent("greedy"))
    run_dir = write_run(profile, records, suite, out_root=str(tmp_path))
    payload = json.loads((run_dir / "run.json").read_text(encoding="utf-8"))

    assert set(payload["agent"]) == {"name", "version", "config_hash"}
    assert payload["agent"]["name"] == "greedy"
    assert payload["agent"]["version"] == "0"  # default when no agent object is supplied
    assert payload["agent"]["config_hash"] == config_hash({})


def test_runlog_existing_fields_intact(tmp_path):
    # The schema bump is additive: all pre-existing top-level + per-match fields remain,
    # and the original trailing positions (suite, profile, matches) are unchanged.
    suite = Suite(seed=1, n_scenarios=2)
    agent = make_agent("heuristic")
    profile, records = run_suite(suite, agent)
    run_dir = write_run(profile, records, suite, out_root=str(tmp_path), agent=agent)
    payload = json.loads((run_dir / "run.json").read_text(encoding="utf-8"))

    # Top-level: every prior key still present; the original three stay last and in order.
    assert {"schema_version", "off_record", "suite", "profile", "matches"}.issubset(payload)
    assert list(payload.keys())[-3:] == ["suite", "profile", "matches"]
    # The new identity block sits among the additive leading keys, not the trailing ones.
    assert "agent" in payload

    # Profile block unchanged.
    assert {"agent", "efficiency", "own_value", "deal_rate", "per_persona"}.issubset(
        payload["profile"]
    )
    # Per-match fields unchanged.
    keys = list(payload["matches"][0].keys())
    assert {
        "scenario_seed", "n_issues", "n_levels", "persona", "agreed", "outcome",
        "efficiency", "own_value", "turns_used", "transcript", "analysis", "off_record",
    }.issubset(keys)
