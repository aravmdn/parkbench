"""Benchmark versioning (D-061): every JSON result the CLI emits carries `benchmark_version`.

A stored/shared score is meaningless without knowing which generation of scenario generators and
scoring produced it. These tests pin the stamp's shape and assert every ``--json`` emission point
(radar, career, leaderboard, validity) routes through it — cheaply, by stubbing the heavy builders —
plus one real end-to-end radar run.
"""

from __future__ import annotations

import json
import re

import parkbench
from parkbench import cli


def test_benchmark_version_is_a_semver_string():
    assert re.fullmatch(r"\d+\.\d+\.\d+", parkbench.BENCHMARK_VERSION)


def test_emit_json_stamps_the_version_first_and_leaves_the_payload_intact(capsys):
    cli._emit_json({"a": 1, "nested": {"b": [2, 3]}})
    out = json.loads(capsys.readouterr().out)
    assert next(iter(out)) == "benchmark_version"  # provenance up front, eyeball-able
    assert out.pop("benchmark_version") == parkbench.BENCHMARK_VERSION
    assert out == {"a": 1, "nested": {"b": [2, 3]}}  # the stamp is the ONLY change


class _StubProfile:
    """Just enough surface for cmd_radar/cmd_career/cmd_leaderboard/cmd_validity's --json paths."""

    agent = "stub"
    career_score = 1.0

    def to_dict(self):
        return {"agent": "stub"}


def test_every_json_command_is_stamped(monkeypatch, capsys):
    """All four --json emission points carry the version (heavy builders stubbed for speed)."""
    import parkbench.career
    import parkbench.radar
    import parkbench.validity

    monkeypatch.setattr(parkbench.radar, "build_radar", lambda *a, **k: _StubProfile())
    monkeypatch.setattr(parkbench.career, "build_career", lambda *a, **k: _StubProfile())
    monkeypatch.setattr(
        parkbench.validity, "build_validity_report", lambda *a, **k: _StubProfile()
    )
    for argv in (
        ["radar", "--agent", "heuristic", "--json"],
        ["career", "--agent", "heuristic", "--json"],
        ["leaderboard", "--agents", "heuristic", "--json"],
        ["validity", "--json"],
    ):
        assert cli.main(argv) == 0
        out = json.loads(capsys.readouterr().out)
        assert out["benchmark_version"] == parkbench.BENCHMARK_VERSION, argv


def test_radar_json_end_to_end_is_stamped_and_otherwise_unchanged(capsys):
    """One real CLI run: the emitted JSON is exactly build_radar(...).to_dict() + the stamp."""
    from parkbench.radar import build_radar

    assert cli.main(["radar", "--agent", "random", "--seed", "1", "--json"]) == 0
    out = json.loads(capsys.readouterr().out)
    assert out.pop("benchmark_version") == parkbench.BENCHMARK_VERSION
    # Round-trip the direct build through JSON too (tuples become lists), then require equality.
    expected = json.loads(json.dumps(build_radar("random", seed=1).to_dict()))
    assert out == expected
