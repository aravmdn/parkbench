"""The live BYO connector (chunk-4 ``byo-live-connector``).

The central claim: a BYO agent driven over the **real** ``docs/09`` HTTP wire produces the same
negotiation result the in-process :class:`~parkbench.rides.NegotiationRide` produces — so the world's
BYO trainer can be fed live protocol traffic instead of a hand-authored fixture without inventing a
second scoring path (D-012). The second claim is honesty: the wire scores exactly one ride, so the
captured profile covers exactly one axis and says so.

Everything runs in-process on an ephemeral loopback port (``port=0``); no external network.
"""

from __future__ import annotations

import json

from parkbench import BENCHMARK_VERSION, cli
from parkbench.agents import make_agent
from parkbench.byo import (
    DEFAULT_BYO_NAME,
    ByoRun,
    render_byo_run,
    run_byo_from_name,
    run_byo_negotiation,
)
from parkbench.radar import build_radar
from parkbench.rides import RIDE_REGISTRY, NegotiationRide

# One suite run per call crosses a socket ~190 times, so the shared fixtures below are built once
# per module rather than per test (a plain module-level cache keeps this dependency-free).
_CACHE: dict[tuple, ByoRun] = {}


def _run(agent_name: str = "heuristic", seed: int = 1, **kwargs) -> ByoRun:
    key = (agent_name, seed, tuple(sorted(kwargs.items())))
    if key not in _CACHE:
        _CACHE[key] = run_byo_from_name(agent_name, seed=seed, **kwargs)
    return _CACHE[key]


# --- the wire reproduces the in-process ride ----------------------------------------------


def test_wired_run_matches_the_in_process_negotiation_ride():
    """A run over the socket == the same agent's in-process ride result, detail for detail.

    This is the load-bearing test: it is what makes a live BYO profile comparable to a baseline's,
    and it proves the connector transports rather than re-scores.
    """
    wired = _run("heuristic", seed=1)
    in_process = NegotiationRide().evaluate("heuristic", 1)

    leg = wired.profile.results[0]
    assert leg.score == in_process.score
    assert leg.detail == in_process.detail
    assert leg.ride == "negotiation"
    assert leg.axis == "social"


def test_wired_run_matches_the_in_process_ride_for_a_seed_dependent_agent():
    """`random` re-seeds per match, so parity here proves the `new_match` re-seed hop works."""
    wired = _run("random", seed=3)
    assert wired.profile.results[0].score == NegotiationRide().evaluate("random", 3).score


def test_payload_is_deterministic():
    """Same agent + same seed => byte-identical JSON. No clock, no port, no run-to-run drift."""
    first = run_byo_from_name("heuristic", seed=2).to_dict()
    second = run_byo_from_name("heuristic", seed=2).to_dict()
    assert json.dumps(first, sort_keys=True) == json.dumps(second, sort_keys=True)
    payload = json.dumps(first)
    assert "captured_at" not in payload and "timestamp" not in payload
    # The ephemeral port is run mechanics, never run results.
    assert "port" not in payload


# --- the profile is honest about what the wire could measure -------------------------------


def test_profile_covers_only_the_social_axis():
    """The v1 wire carries negotiation only, so exactly one axis is covered and three are missing."""
    run = _run("heuristic", seed=1)
    assert run.profile.covered_axes == ["social"]
    assert run.profile.missing_axes == ["economic", "coding", "safety"]
    payload = run.to_dict()
    assert set(payload["axes"]) == {"social"}
    assert payload["missing_axes"] == ["economic", "coding", "safety"]


def test_every_other_registered_ride_is_reported_skipped():
    """Rides the wire cannot reach are named, not silently dropped — and the list tracks the registry."""
    run = _run("heuristic", seed=1)
    expected = [name for name in RIDE_REGISTRY if name != "negotiation"]
    assert run.profile.skipped == expected
    assert run.to_dict()["skipped_rides"] == expected


def test_payload_carries_the_byo_and_live_markers():
    payload = _run("heuristic", seed=1).to_dict()
    assert payload["byo"] is True
    assert payload["live"] is True
    assert payload["agent"] == DEFAULT_BYO_NAME


def test_source_block_records_structural_wire_provenance():
    payload = _run("heuristic", seed=1).to_dict()
    source = payload["source"]
    assert source["mode"] == "live"
    assert source["protocol"] == "http/json"
    assert source["spec"] == "docs/09-byo-protocol.md"
    assert source["ride"] == "negotiation"
    # 12 scenarios x 4 house personas, and one answered turn per act() across the wire.
    assert source["matches"] == 48
    assert source["turns"] > 0
    assert source["driver"] == "heuristic"


def test_payload_shape_matches_a_radar_payload():
    """The front-end reads one shape: a BYO payload is a radar payload plus the BYO markers."""
    byo = _run("heuristic", seed=1).to_dict()
    radar = build_radar("heuristic", seed=1).to_dict()
    assert set(radar).issubset(set(byo))


# --- identity (D-038) ----------------------------------------------------------------------


def test_identity_uses_the_byo_label_and_the_driven_agents_real_config_hash():
    run = run_byo_negotiation(make_agent("heuristic"), seed=1, byo_name="acme-bot", byo_version="0.3.1")
    identity = run.identity
    assert identity.name == "acme-bot"
    assert identity.version == "0.3.1"
    # The hash is the driven agent's own, so a differently-configured BYO agent stays distinguishable.
    assert identity.config_hash == make_agent("heuristic").identity().config_hash
    assert run.to_dict()["identity"] == identity.to_dict()


def test_identity_version_defaults_to_the_driven_agents_version():
    run = _run("heuristic", seed=1)
    assert run.identity.version == make_agent("heuristic").identity().version


def test_distinct_agents_get_distinct_config_hashes():
    # A short suite: this is about who the driver was, not what it scored over 12 scenarios.
    heuristic = run_byo_negotiation(make_agent("heuristic"), seed=1, n_scenarios=3)
    greedy = run_byo_negotiation(make_agent("greedy"), seed=1, n_scenarios=3)
    assert heuristic.identity.config_hash != greedy.identity.config_hash or (
        # Both are parameterless today; then the *scores* must still differ (different behaviour).
        heuristic.score != greedy.score
    )


# --- rendering + suite knobs ---------------------------------------------------------------


def test_render_names_the_missing_axes_rather_than_hiding_them():
    text = render_byo_run(_run("heuristic", seed=1))
    assert "acme-bot" in text
    assert "negotiation" in text
    for axis in ("economic", "coding", "safety"):
        assert axis in text
    assert "docs/09-byo-protocol.md" in text


def test_scenario_count_is_honoured():
    run = run_byo_from_name("heuristic", seed=1, n_scenarios=2)
    assert run.n_scenarios == 2
    assert run.to_dict()["source"]["matches"] == 8  # 2 scenarios x 4 personas


def test_run_writes_no_log_by_default(tmp_path, monkeypatch):
    """A captured profile must not litter `runs/` — logging is opt-in for the connector."""
    monkeypatch.chdir(tmp_path)
    run_byo_from_name("heuristic", seed=1, n_scenarios=1)
    assert not (tmp_path / "runs").exists()


# --- the CLI surface (`parkbench byo-run`) -------------------------------------------------


def test_cli_json_is_the_connector_payload_plus_the_version_stamp(capsys):
    assert cli.main(["byo-run", "--scenarios", "2", "--json"]) == 0
    out = json.loads(capsys.readouterr().out)
    assert out.pop("benchmark_version") == BENCHMARK_VERSION
    assert out == run_byo_from_name("heuristic", seed=1, n_scenarios=2).to_dict()


def test_cli_text_output_names_what_the_wire_could_not_measure(capsys):
    assert cli.main(["byo-run", "--scenarios", "2"]) == 0
    out = capsys.readouterr().out
    assert "BYO live run" in out
    assert "missing axes" in out
    assert "negotiation" in out


def test_cli_out_writes_a_drop_in_fixture(tmp_path, capsys):
    target = tmp_path / "nested" / "radar-byo-live.json"
    assert cli.main(["byo-run", "--scenarios", "2", "--out", str(target)]) == 0
    capsys.readouterr()

    raw = target.read_bytes()
    assert b"\r\n" not in raw  # canonical LF, like every exported fixture
    assert raw.endswith(b"\n")
    payload = json.loads(raw.decode("utf-8"))
    # Same stamped shape the fixtures carry, so it drops into web/src/fixtures/ as-is.
    assert payload["benchmark_version"] == BENCHMARK_VERSION
    assert payload["byo"] is True and payload["live"] is True
    assert payload["axes"]["social"] > 0


def test_cli_labels_flow_into_the_identity(capsys):
    argv = ["byo-run", "--scenarios", "2", "--name", "acme-bot-2", "--byo-version", "9.9", "--json"]
    assert cli.main(argv) == 0
    out = json.loads(capsys.readouterr().out)
    assert out["agent"] == "acme-bot-2"
    assert out["identity"] == {
        "name": "acme-bot-2",
        "version": "9.9",
        "config_hash": make_agent("heuristic").identity().config_hash,
    }
