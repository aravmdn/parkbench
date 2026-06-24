"""The spectator-fixture export command (chunk-3 `live-profiles`, engine half).

`parkbench export-profiles <out-dir>` regenerates every committed spectator fixture — the four
`web/` radar fixtures + the `web/` leaderboard, and the three `viewer/` bundled samples — each
byte-identical to the corresponding single `parkbench ... --json` command (including the D-061
`benchmark_version` stamp), because it captures the *existing* CLI paths rather than re-serializing.

Following `test_versioning.py`, the heavy per-ride builders are stubbed (agent- and seed-sensitive
stubs, so wrong-agent / wrong-seed wiring would be caught) — byte-identity against the real engine
output is a property of the shared code path, verified end-to-end outside the suite.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

import parkbench
from parkbench import cli

EXPECTED_FILES = (
    "web/src/fixtures/radar-heuristic.json",
    "web/src/fixtures/radar-greedy.json",
    "web/src/fixtures/radar-optimal.json",
    "web/src/fixtures/radar-random.json",
    "web/src/fixtures/leaderboard.json",
    "viewer/sample-radar.json",
    "viewer/sample-career.json",
    "viewer/sample-leaderboard.json",
)

# The single command whose stdout each exported file must equal, byte for byte.
FILE_TO_ARGV = {
    "web/src/fixtures/radar-heuristic.json": ["radar", "--agent", "heuristic", "--json"],
    "web/src/fixtures/radar-greedy.json": ["radar", "--agent", "greedy", "--json"],
    "web/src/fixtures/radar-optimal.json": ["radar", "--agent", "optimal", "--json"],
    "web/src/fixtures/radar-random.json": ["radar", "--agent", "random", "--json"],
    "web/src/fixtures/leaderboard.json": ["leaderboard", "--json"],
    "viewer/sample-radar.json": ["radar", "--agent", "heuristic", "--json"],
    "viewer/sample-career.json": ["career", "--agent", "greedy", "--json"],
    "viewer/sample-leaderboard.json": ["leaderboard", "--json"],
}

# Distinct, deterministic career scores so the stubbed leaderboard has a stable, non-trivial order.
_SCORES = {"random": 0.2, "greedy": 0.1, "heuristic": 0.5, "optimal": 1.0}


class _StubRadar:
    def __init__(self, agent: str, seed: int):
        self.agent, self.seed = agent, seed

    def to_dict(self) -> dict:
        return {"agent": self.agent, "seed": self.seed, "kind": "radar"}


class _StubCareer:
    def __init__(self, agent: str, seed: int):
        self.agent, self.seed = agent, seed
        self.career_score = _SCORES[agent]

    def to_dict(self) -> dict:
        return {"agent": self.agent, "seed": self.seed, "career_score": self.career_score}


@pytest.fixture()
def stub_builders(monkeypatch):
    """Replace the heavy per-ride builders with cheap agent/seed-sensitive stubs."""
    import parkbench.career
    import parkbench.radar

    monkeypatch.setattr(
        parkbench.radar, "build_radar", lambda agent, seed=1, **k: _StubRadar(agent, seed)
    )
    monkeypatch.setattr(
        parkbench.career, "build_career", lambda agent, seed=1, **k: _StubCareer(agent, seed)
    )


def _export(tmp_path: Path, capsys, extra: list[str] | None = None) -> str:
    assert cli.main(["export-profiles", str(tmp_path)] + (extra or [])) == 0
    return capsys.readouterr().out


def test_export_writes_all_fixtures_byte_identical_to_single_commands(
    stub_builders, tmp_path, capsys
):
    summary = _export(tmp_path, capsys)
    # All 8 files exist, and the summary names each one on its own line.
    for rel in EXPECTED_FILES:
        assert (tmp_path / rel).is_file(), rel
        assert sum(1 for line in summary.splitlines() if str(tmp_path / rel) in line) == 1, rel
    assert sum(1 for line in summary.splitlines() if line.startswith("  wrote ")) == len(
        EXPECTED_FILES
    )
    # Each file is byte-for-byte the corresponding single command's stdout.
    for rel, argv in FILE_TO_ARGV.items():
        assert cli.main(argv) == 0
        expected = capsys.readouterr().out.encode("utf-8")
        assert (tmp_path / rel).read_bytes() == expected, rel


def test_export_is_deterministic(stub_builders, tmp_path, capsys):
    _export(tmp_path / "a", capsys)
    _export(tmp_path / "b", capsys)
    for rel in EXPECTED_FILES:
        assert (tmp_path / "a" / rel).read_bytes() == (tmp_path / "b" / rel).read_bytes(), rel


def test_export_stamps_benchmark_version_in_every_file(stub_builders, tmp_path, capsys):
    _export(tmp_path, capsys)
    for rel in EXPECTED_FILES:
        payload = json.loads((tmp_path / rel).read_text(encoding="utf-8"))
        assert next(iter(payload)) == "benchmark_version", rel  # first key, per D-061
        assert payload["benchmark_version"] == parkbench.BENCHMARK_VERSION, rel


def test_export_passes_seed_through_to_the_builders(stub_builders, tmp_path, capsys):
    _export(tmp_path, capsys, ["--seed", "7"])
    for rel in EXPECTED_FILES:
        payload = json.loads((tmp_path / rel).read_text(encoding="utf-8"))
        # radar/career carry the stub's seed; the leaderboard payload carries it top-level too.
        assert payload["seed"] == 7, rel


def test_export_end_to_end_real_engine(tmp_path, capsys):
    """One real (unstubbed) export: spot-check two files against their real single commands."""
    _export(tmp_path, capsys)
    for rel in ("web/src/fixtures/radar-random.json", "viewer/sample-career.json"):
        assert cli.main(FILE_TO_ARGV[rel]) == 0
        assert (tmp_path / rel).read_bytes() == capsys.readouterr().out.encode("utf-8"), rel
        payload = json.loads((tmp_path / rel).read_text(encoding="utf-8"))
        assert payload["benchmark_version"] == parkbench.BENCHMARK_VERSION
