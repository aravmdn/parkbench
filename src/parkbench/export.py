"""``parkbench export-profiles`` — regenerate the committed spectator fixtures from the versioned CLI.

The `web/` front-end and the static `viewer/` pages are **presentation-only** (D-012): they render
*verbatim* CLI ``--json`` output — they never compute a score. Those fixtures used to be refreshed by
hand (re-run each ``parkbench ... --json`` command, redirect into the right file), which is
error-prone and easy to leave stale (the pre-commons ``sample-radar.json`` drifted for weeks). This
module turns the whole refresh into one reproducible, testable command::

    parkbench export-profiles            # (re)write every fixture from the current engine
    parkbench export-profiles --check    # verify committed fixtures still match (drift => exit 1)

Every emitted file holds the **verbatim** ``parkbench <cmd> --json`` output — same producers
(:func:`parkbench.radar.build_radar` / :func:`parkbench.career.build_career` /
:func:`parkbench.career.build_leaderboard`), same ``benchmark_version`` stamp (D-061), same 2-space
indent + trailing newline. So the exporter invents no data; it just automates provenance.

**Provenance is compared semantically, not byte-for-byte.** A committed fixture generated on one
machine and re-generated on another can differ in the last digit of an *unrounded* float
(e.g. ``0.1002070438502885`` vs ``0.10020704385028849`` — the same value, printed one ULP apart):
float64 arithmetic is IEEE-754-deterministic, but shortest-repr can differ across CPython builds. So
``--check`` (and the tests) parse both sides and round every float to :data:`_COMPARE_DP` decimals
before comparing — collapsing that sub-display noise while still catching any *real* drift (a changed
score, a stale pre-commons axis, a missing key: all differ far above 1e-12). Line endings are
normalized too (git's stored form is LF; ``core.autocrlf`` may show CRLF in a Windows working tree),
so results are identical on Windows and Linux.

This is engine-adjacent CLI surface only — no ride or scoring code is touched, and the ``--check``
guard lets a test pin the committed fixtures to the CLI forever (see ``tests/test_export.py``).
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from . import BENCHMARK_VERSION

DEFAULT_SEED = 1

# Compare fixtures to this many decimals: below any real score change (top-level scores are already
# rounded to 6 dp), far above float64 last-ULP repr noise (~1e-16 near 1.0). See the module docstring.
_COMPARE_DP = 12


@dataclass(frozen=True)
class FixtureSpec:
    """One committed fixture and the CLI ``--json`` invocation that reproduces it.

    ``kind`` is ``"radar"``, ``"career"`` or ``"leaderboard"``; ``agent`` names the subject for
    radar/career (``None`` for the leaderboard, which ranks the default roster). ``path`` is
    repo-relative (joined under the export root).
    """

    path: str
    kind: str
    agent: str | None = None


# The full spectator fixture set. Anything the web app or the viewer pages `fetch`/embed as CLI JSON
# belongs here; hand-maintained-elsewhere files (a run *log* like viewer/sample-run.json, or the
# static viewer/park.html which loads no JSON) deliberately do not — they are not CLI --json output.
FIXTURE_MANIFEST: tuple[FixtureSpec, ...] = (
    # web/ front-end: one radar per baseline + the career leaderboard.
    FixtureSpec("web/src/fixtures/radar-heuristic.json", "radar", "heuristic"),
    FixtureSpec("web/src/fixtures/radar-greedy.json", "radar", "greedy"),
    FixtureSpec("web/src/fixtures/radar-optimal.json", "radar", "optimal"),
    FixtureSpec("web/src/fixtures/radar-random.json", "radar", "random"),
    FixtureSpec("web/src/fixtures/leaderboard.json", "leaderboard", None),
    # viewer/ static pages: a sample radar / career / leaderboard payload.
    FixtureSpec("viewer/sample-radar.json", "radar", "heuristic"),
    FixtureSpec("viewer/sample-career.json", "career", "greedy"),
    FixtureSpec("viewer/sample-leaderboard.json", "leaderboard", None),
)


def _stamp(payload: dict) -> str:
    """Format ``payload`` exactly as the CLI's ``_emit_json`` prints it (stamp + trailing newline).

    Kept identical to ``parkbench.cli._emit_json`` on purpose — a test asserts export output equals
    real CLI output so this can never silently drift.
    """
    return json.dumps({"benchmark_version": BENCHMARK_VERSION, **payload}, indent=2) + "\n"


def render_fixture(spec: FixtureSpec, seed: int = DEFAULT_SEED) -> str:
    """Return the canonical (LF) text for ``spec`` — the exact CLI ``--json`` bytes it should hold."""
    # Imported lazily so importing this module stays cheap (mirrors the CLI's lazy-import style).
    from .career import build_career, build_leaderboard
    from .radar import build_radar

    if spec.kind == "radar":
        return _stamp(build_radar(spec.agent, seed=seed).to_dict())
    if spec.kind == "career":
        return _stamp(build_career(spec.agent, seed=seed).to_dict())
    if spec.kind == "leaderboard":
        ranking = [p.to_dict() for p in build_leaderboard(seed=seed)]
        return _stamp({"seed": seed, "ranking": ranking})
    raise ValueError(f"unknown fixture kind: {spec.kind!r}")


@dataclass
class FixtureResult:
    """Outcome for one fixture after an export/check pass."""

    spec: FixtureSpec
    status: str  # write mode: "written" | "unchanged"; check mode: "ok" | "drift" | "missing"

    @property
    def ok(self) -> bool:
        """True when no action-worthy problem exists (drift/missing are the only failures)."""
        return self.status not in ("drift", "missing")


def _read_normalized(path: Path) -> str | None:
    """Read ``path`` with universal newlines (CRLF/LF both -> LF), or ``None`` if absent."""
    if not path.exists():
        return None
    with open(path, encoding="utf-8", newline=None) as fh:
        return fh.read()


def _round_floats(obj):
    """Recursively round every float in a parsed-JSON structure to :data:`_COMPARE_DP` decimals."""
    if isinstance(obj, float):
        return round(obj, _COMPARE_DP)
    if isinstance(obj, dict):
        return {k: _round_floats(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_round_floats(v) for v in obj]
    return obj


def _semantically_equal(a: str | None, b: str) -> bool:
    """True if two fixture texts encode the same data up to :data:`_COMPARE_DP`-decimal float repr.

    Tolerates cross-platform last-ULP float-repr differences (and line-ending differences, since
    both sides were read/rendered with LF) while catching any real content change.
    """
    if a is None:
        return False
    try:
        return _round_floats(json.loads(a)) == _round_floats(json.loads(b))
    except json.JSONDecodeError:
        return False


def export_profiles(
    root: Path | str = ".",
    seed: int = DEFAULT_SEED,
    check: bool = False,
) -> list[FixtureResult]:
    """Regenerate (or, with ``check=True``, verify) every fixture in :data:`FIXTURE_MANIFEST`.

    In write mode, each file is (over)written with the canonical LF text and reported ``written``
    (content changed / created) or ``unchanged``. In check mode nothing is written: each file is
    compared newline-agnostically and reported ``ok`` / ``drift`` / ``missing``.
    """
    root = Path(root)
    results: list[FixtureResult] = []
    for spec in FIXTURE_MANIFEST:
        target = root / spec.path
        desired = render_fixture(spec, seed=seed)
        current = _read_normalized(target)

        if check:
            if current is None:
                status = "missing"
            elif _semantically_equal(current, desired):
                status = "ok"
            else:
                status = "drift"
        else:
            # Only rewrite genuinely stale/absent files — a semantic match is left untouched so the
            # writer never churns a correct fixture over a cross-platform last-ULP float difference.
            if _semantically_equal(current, desired):
                status = "unchanged"
            else:
                target.parent.mkdir(parents=True, exist_ok=True)
                # Force LF regardless of platform so the committed form matches git's stored bytes.
                with open(target, "w", encoding="utf-8", newline="\n") as fh:
                    fh.write(desired)
                status = "written"

        results.append(FixtureResult(spec, status))
    return results


def render_export_report(results: list[FixtureResult], check: bool, root: Path | str = ".") -> str:
    """Human-readable summary of an export/check pass."""
    root = Path(root)
    verb = "check" if check else "export"
    lines = [f"Parkbench - profile fixture {verb}  (bench v{BENCHMARK_VERSION})", ""]
    for r in results:
        lines.append(f"  [{r.status:<9}] {r.spec.path}")
    lines.append("")
    if check:
        bad = [r for r in results if not r.ok]
        if bad:
            lines.append(
                f"  DRIFT: {len(bad)} fixture(s) do not match the current CLI output. "
                f"Run `parkbench export-profiles` to regenerate."
            )
        else:
            lines.append(f"  OK: all {len(results)} fixtures match the current CLI output.")
    else:
        written = sum(1 for r in results if r.status == "written")
        lines.append(
            f"  wrote {written} / {len(results)} fixture(s) under {root} "
            f"({len(results) - written} already current)."
        )
    return "\n".join(lines)
