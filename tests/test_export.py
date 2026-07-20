"""Fixture exporter (D-062): ``parkbench export-profiles`` regenerates the committed spectator
fixtures from the versioned CLI, and ``--check`` pins them to it forever.

These tests are the standing provenance guard: every committed ``web/src/fixtures/*.json`` and
``viewer/sample-*.json`` must equal what the current engine's ``--json`` producers emit (so a stale
fixture — like the pre-commons ``sample-radar.json`` that once drifted for weeks — can never ship
again unnoticed), the write→check round-trips, and drift/missing files fail the check with a nonzero
exit. Comparison is float-repr-tolerant (see ``export._COMPARE_DP``) so it passes on any platform.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

import parkbench
from parkbench import cli
from parkbench.export import (
    FIXTURE_MANIFEST,
    export_profiles,
    render_fixture,
)

REPO_ROOT = Path(__file__).resolve().parent.parent


# --------------------------------------------------------------------------------------------------
# Provenance: the committed tree matches the current CLI
# --------------------------------------------------------------------------------------------------


def test_manifest_covers_the_committed_web_and_viewer_fixtures():
    """The manifest lists exactly the committed CLI-json fixtures under web/ and viewer/."""
    listed = {spec.path.replace("\\", "/") for spec in FIXTURE_MANIFEST}
    on_disk = {
        p.relative_to(REPO_ROOT).as_posix()
        for p in list((REPO_ROOT / "web" / "src" / "fixtures").glob("*.json"))
        + list((REPO_ROOT / "viewer").glob("sample-*.json"))
        # sample-run.json is a run *log*, not CLI --json output, so it is deliberately not exported.
        if p.name != "sample-run.json"
    }
    assert listed == on_disk


@pytest.mark.parametrize("spec", FIXTURE_MANIFEST, ids=lambda s: s.path)
def test_committed_fixture_matches_current_cli_output(spec):
    """Every committed fixture is (semantically) what the current engine's --json producers emit."""
    committed = (REPO_ROOT / spec.path).read_text(encoding="utf-8")
    fresh = render_fixture(spec)
    assert json.loads(committed) == json.loads(fresh) or _rounded(committed) == _rounded(fresh)


def test_check_passes_on_the_committed_tree():
    results = export_profiles(root=REPO_ROOT, check=True)
    bad = [r.spec.path for r in results if not r.ok]
    assert bad == [], f"fixtures drifted from the CLI: {bad}"
    assert cli.main(["export-profiles", "--root", str(REPO_ROOT), "--check"]) == 0


# --------------------------------------------------------------------------------------------------
# The exporter is verbatim CLI output (DRY guard against format drift)
# --------------------------------------------------------------------------------------------------


def test_render_fixture_equals_real_cli_json(capsys):
    """render_fixture must equal the actual CLI --json print (stamp, indent, roster, ordering)."""
    cases = [
        (["radar", "--agent", "greedy", "--seed", "1", "--json"], "radar", "greedy"),
        (["leaderboard", "--seed", "1", "--json"], "leaderboard", None),
    ]
    for argv, kind, agent in cases:
        assert cli.main(argv) == 0
        cli_out = capsys.readouterr().out
        spec = next(s for s in FIXTURE_MANIFEST if s.kind == kind and s.agent == agent)
        assert json.loads(cli_out) == json.loads(render_fixture(spec)), argv


def test_every_fixture_carries_the_benchmark_version():
    for spec in FIXTURE_MANIFEST:
        payload = json.loads(render_fixture(spec))
        assert payload["benchmark_version"] == parkbench.BENCHMARK_VERSION


# --------------------------------------------------------------------------------------------------
# Write → check round-trip, drift/missing detection, canonical newlines
# --------------------------------------------------------------------------------------------------


def test_write_then_check_roundtrips(tmp_path):
    first = export_profiles(root=tmp_path, check=False)
    assert all(r.status == "written" for r in first)  # fresh dir: everything created

    check = export_profiles(root=tmp_path, check=True)
    assert all(r.status == "ok" for r in check)

    second = export_profiles(root=tmp_path, check=False)
    assert all(r.status == "unchanged" for r in second)  # idempotent: no needless rewrites


def test_written_fixtures_use_canonical_lf_newlines(tmp_path):
    export_profiles(root=tmp_path, check=False)
    for spec in FIXTURE_MANIFEST:
        raw = (tmp_path / spec.path).read_bytes()
        assert b"\r" not in raw, f"{spec.path} was written with CR (want canonical LF)"
        assert raw.endswith(b"\n")


def test_check_detects_drift_and_exits_nonzero(tmp_path):
    export_profiles(root=tmp_path, check=False)
    # Corrupt one fixture well beyond float-repr tolerance.
    victim = tmp_path / "web" / "src" / "fixtures" / "radar-random.json"
    payload = json.loads(victim.read_text())
    payload["axes"]["economic"] = 0.123456  # a real, visible change
    victim.write_text(json.dumps(payload, indent=2) + "\n")

    results = {r.spec.path.replace("\\", "/"): r for r in export_profiles(root=tmp_path, check=True)}
    assert results["web/src/fixtures/radar-random.json"].status == "drift"
    assert cli.main(["export-profiles", "--root", str(tmp_path), "--check"]) == 1


def test_check_reports_missing_and_exits_nonzero(tmp_path):
    export_profiles(root=tmp_path, check=False)
    (tmp_path / "viewer" / "sample-career.json").unlink()
    results = {r.spec.path.replace("\\", "/"): r for r in export_profiles(root=tmp_path, check=True)}
    assert results["viewer/sample-career.json"].status == "missing"
    assert cli.main(["export-profiles", "--root", str(tmp_path), "--check"]) == 1


# --------------------------------------------------------------------------------------------------
# helpers
# --------------------------------------------------------------------------------------------------


def _rounded(text: str):
    from parkbench.export import _round_floats

    return _round_floats(json.loads(text))
