"""``parkbench doctor`` — diagnose the local setup and say where every setting comes from (D-072).

Motivated by D-068, which cost a session to a setup that *looked* fine and silently was not: the
default free model had been retired upstream (so every ``--agent llm`` run quietly printed heuristic
fallback numbers), and an ``OPENROUTER_API_KEY`` in the **OS environment** was silently shadowing a
different key in the gitignored ``.env`` — with **no single command** that could answer "is my setup
actually live, and where is each setting coming from?". This module is that command.

What it reports:

- **Runtime** — Python, the imported ``parkbench`` package's location + whether it is an *editable*
  install, and :data:`parkbench.BENCHMARK_VERSION`. (The location line catches the classic
  git-worktree trap: standing in one checkout while ``import parkbench`` resolves to another.)
- **Config provenance** — for every setting the project reads, the **source of the effective value**:
  the OS environment, the ``.env`` file, or the in-code default; and an explicit warning when a
  ``.env`` value is being **shadowed** by a different OS-environment value. That single line is what
  would have saved the D-068 session. Provenance comes from :mod:`parkbench.dotenv`'s load record
  (:func:`parkbench.dotenv.last_load`), because after the CLI has loaded the ``.env`` a file-sourced
  value is otherwise indistinguishable from an OS-env one.
- **Secrets hygiene** — a secret's *content is never emitted*, by this module or its ``--json``.
  Only presence, source, character count and a shape hint are reported, and any secret value is
  scrubbed out of borrowed text (e.g. a provider error message) before it is shown.
- **Model** — the effective model id for the bare ``llm`` agent and where it came from.
- **Fixture provenance** — the existing :func:`parkbench.export.export_profiles` ``--check`` logic,
  reused verbatim (never reimplemented), so drifted spectator fixtures are caught here too.
- **``--live`` (opt-in)** — makes **one** cheap OpenRouter call *through the real*
  :class:`parkbench.agents.llm.LLMAgent` path (same provider, prompt and parser a scored run uses —
  not a parallel implementation) and reports whether the agent is genuinely live or silently falling
  back. **Without ``--live`` this command makes zero network calls.**

Exit code: ``0`` unless something is *actually broken* — fixture drift/missing, or a ``--live`` probe
that did not reach a model. Advisory findings (no API key, a shadowed ``.env`` value, a package
imported from another tree) are **warnings**: they colour the report, not the exit code.

Stdlib-only (D-023/D-030), deterministic, and purely additive: no ride, scoring, fixture or
``BENCHMARK_VERSION`` change — reporting only.
"""

from __future__ import annotations

import json
import os
import platform
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from . import BENCHMARK_VERSION, __version__
from . import dotenv as _dotenv

# Statuses, worst-last. Only FAIL moves the exit code.
OK, WARN, FAIL, SKIP = "ok", "warn", "fail", "skip"
_SEVERITY = {SKIP: 0, OK: 1, WARN: 2, FAIL: 3}

REDACTED = "***"


@dataclass(frozen=True)
class SettingSpec:
    """One environment-driven setting the project reads, and how to describe it."""

    name: str
    purpose: str
    secret: bool = False
    #: Human description of the in-code default used when neither env nor `.env` supplies a value.
    default_desc: str = "unset"
    #: Warn when absent? False for settings that fall back to a documented in-code default — an
    #: unset optional knob is normal, and a report that cries wolf about it stops being read.
    warn_if_absent: bool = False


def _default_model() -> str:
    # Imported lazily: `doctor` must not drag the LLM agent in unless it is describing it.
    from .agents.llm import DEFAULT_MODEL

    return DEFAULT_MODEL


#: Every environment variable the engine itself reads (grep `os.environ` in `src/parkbench/`). The
#: coding sandbox's bootstrap allowlist (D-048) is reported separately — those are OS-provided, not
#: Parkbench settings.
SETTINGS: tuple[SettingSpec, ...] = (
    SettingSpec(
        "OPENROUTER_API_KEY",
        purpose="OpenRouter API key for live `--agent llm` runs (one key reaches every model).",
        secret=True,
        default_desc="unset (absent => the llm agent falls back to the deterministic heuristic)",
        warn_if_absent=True,
    ),
    SettingSpec(
        "OPENROUTER_MODEL",
        purpose="Model id for the bare `llm` agent (a pinned `llm:<id>` variant ignores it).",
        default_desc="DEFAULT_MODEL in agents/llm.py",
    ),
)

#: Bootstrap variables the coding ride copies into its sandboxed child process (D-048). Reported by
#: presence only (names, never values) — a missing PATH is the one that actually breaks the ride.
_SANDBOX_CRITICAL = ("PATH",)


def _redact(text: str, secrets: tuple[str, ...]) -> str:
    """Scrub every non-empty secret value out of ``text`` (defence in depth for borrowed strings)."""
    for s in secrets:
        if s:
            text = text.replace(s, REDACTED)
    return text


def _known_secrets(load: _dotenv.DotenvLoad) -> tuple[str, ...]:
    """Every secret value this process can see, for redaction.

    Deliberately includes the **shadowed** `.env` value as well as the effective one: a shadowed key
    is still a real credential sitting on disk, and a borrowed error string could quote it. Scrubbing
    only the value in use would leak the other one.
    """
    values: list[str] = []
    for spec in SETTINGS:
        if not spec.secret:
            continue
        for candidate in (
            os.environ.get(spec.name),
            load.loaded.get(spec.name),
            load.shadowed.get(spec.name),
        ):
            if candidate and candidate not in values:
                values.append(candidate)
    return tuple(values)


@dataclass(frozen=True)
class Check:
    """One named diagnosis line with a status and a human-readable detail."""

    name: str
    status: str
    detail: str

    def to_dict(self) -> dict:
        return {"name": self.name, "status": self.status, "detail": self.detail}


@dataclass(frozen=True)
class SettingReport:
    """The effective value of one :class:`SettingSpec`, and where it came from.

    ``value`` is ``None`` for a secret — presence, ``source`` and ``length`` are all that is ever
    reported for one (secrets hygiene). ``shadowed`` means the ``.env`` declares this key but the OS
    environment already owned it, so the file's value is unused; ``shadow_differs`` means the two
    values are actually different — the case that silently misleads (D-068).
    """

    name: str
    present: bool
    source: str  # "OS env" | ".env" | "default" | "unset"
    value: Optional[str]
    length: Optional[int]
    secret: bool
    in_dotenv: bool
    shadowed: bool
    shadow_differs: bool
    note: str = ""

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "present": self.present,
            "source": self.source,
            "value": self.value,  # always null for secrets
            "length": self.length,
            "secret": self.secret,
            "in_dotenv": self.in_dotenv,
            "shadowed": self.shadowed,
            "shadow_differs": self.shadow_differs,
            "note": self.note,
        }

    def describe(self) -> str:
        """One scannable line: never the secret's content, only presence/source/length/shape."""
        if not self.present:
            bits = [f"absent - source: {self.source}"]
        elif self.secret:
            bits = [f"present - source: {self.source} - {self.length} chars"]
        else:
            bits = [f"{self.value} - source: {self.source}"]
        if self.shadowed:
            bits.append(
                ".env value SHADOWED (differs)" if self.shadow_differs
                else ".env value shadowed (same value)"
            )
        if self.note:
            bits.append(self.note)
        return " - ".join(bits)


@dataclass
class DoctorReport:
    """The whole diagnosis: runtime, config provenance, fixtures, and the optional live probe."""

    benchmark_version: str = BENCHMARK_VERSION
    runtime: dict = field(default_factory=dict)
    dotenv: dict = field(default_factory=dict)
    settings: list[SettingReport] = field(default_factory=list)
    model: dict = field(default_factory=dict)
    fixtures: dict = field(default_factory=dict)
    live: Optional[dict] = None
    checks: list[Check] = field(default_factory=list)

    @property
    def status(self) -> str:
        """Worst status across every check (``ok`` when there are none)."""
        worst = OK
        for c in self.checks:
            if _SEVERITY[c.status] > _SEVERITY[worst]:
                worst = c.status
        return worst

    @property
    def exit_code(self) -> int:
        """``1`` iff at least one check actually failed; warnings never fail the command."""
        return 1 if any(c.status == FAIL for c in self.checks) else 0

    def to_dict(self) -> dict:
        return {
            "runtime": self.runtime,
            "dotenv": self.dotenv,
            "settings": [s.to_dict() for s in self.settings],
            "model": self.model,
            "fixtures": self.fixtures,
            "live": self.live,
            "checks": [c.to_dict() for c in self.checks],
            "status": self.status,
            "exit_code": self.exit_code,
        }


# ---------------------------------------------------------------------------------------------
# Runtime
# ---------------------------------------------------------------------------------------------


def _editable_install() -> Optional[bool]:
    """True/False if the installed ``parkbench`` distribution's editability is knowable, else None.

    Reads PEP 610 ``direct_url.json`` (``dir_info.editable``) from the installed distribution's
    metadata. ``None`` means "no installed distribution found" — e.g. running straight from a source
    tree on ``PYTHONPATH``.
    """
    try:
        from importlib.metadata import PackageNotFoundError, distribution
    except ImportError:  # pragma: no cover - importlib.metadata is stdlib on every supported Python
        return None
    try:
        raw = distribution("parkbench").read_text("direct_url.json")
    except (PackageNotFoundError, OSError, ValueError):  # pragma: no cover - env-specific
        return None
    if not raw:
        return False
    try:
        return bool(json.loads(raw).get("dir_info", {}).get("editable", False))
    except ValueError:  # pragma: no cover - malformed metadata
        return None


def _runtime_info(root: Path) -> tuple[dict, list[Check]]:
    """Describe the interpreter + which ``parkbench`` source tree is actually imported."""
    pkg_dir = Path(__file__).resolve().parent
    local_pkg = (root / "src" / "parkbench").resolve()
    # Only meaningful when we are standing in a Parkbench source checkout: if this directory has a
    # `src/parkbench/` but the imported package lives elsewhere, every run/test here is silently
    # exercising a DIFFERENT tree (the git-worktree trap).
    checkout = local_pkg.is_dir()
    same_tree = (pkg_dir == local_pkg) if checkout else None
    editable = _editable_install()

    info = {
        "python_version": platform.python_version(),
        "python_implementation": platform.python_implementation(),
        "executable": sys.executable,
        "platform": platform.platform(terse=True),
        "package_version": __version__,
        "package_path": str(pkg_dir),
        "editable_install": editable,
        "cwd": str(root.resolve()),
        "is_source_checkout": checkout,
        "imports_local_source": same_tree,
        "benchmark_version": BENCHMARK_VERSION,
    }

    checks: list[Check] = [
        Check(
            "python",
            OK,
            f"{platform.python_implementation()} {platform.python_version()} - {sys.executable}",
        )
    ]
    kind = (
        "editable install" if editable
        else "non-editable install" if editable is False
        else "no installed distribution (source on sys.path)"
    )
    if checkout and same_tree is False:
        checks.append(
            Check(
                "package source",
                WARN,
                f"imported from {pkg_dir} but this checkout is {local_pkg} - runs/tests here "
                f"exercise the OTHER tree ({kind}); fix with `uv pip install -e \".[dev]\"`",
            )
        )
    else:
        where = "this checkout" if same_tree else str(pkg_dir)
        checks.append(Check("package source", OK, f"parkbench {__version__} - {where} ({kind})"))
    checks.append(Check("benchmark version", OK, BENCHMARK_VERSION))

    missing = [v for v in _SANDBOX_CRITICAL if v not in os.environ]
    if missing:
        checks.append(
            Check(
                "coding sandbox env",
                WARN,
                f"{', '.join(missing)} missing from the environment - the coding ride's sandboxed "
                "child (D-048) may fail to start",
            )
        )
    else:
        checks.append(
            Check("coding sandbox env", OK, f"{', '.join(_SANDBOX_CRITICAL)} present (values not shown)")
        )
    return info, checks


# ---------------------------------------------------------------------------------------------
# Config provenance — the headline
# ---------------------------------------------------------------------------------------------


def _resolve_dotenv_load(dotenv_path: Path) -> _dotenv.DotenvLoad:
    """The load record to attribute sources with, without ever re-shadowing a real load.

    Prefer the record from the load the CLI already performed for this same path (``cli.main`` loads
    the ``.env`` before any subcommand runs). Re-loading instead would report every key as
    "shadowed", since the first load already put them in ``os.environ`` — the opposite of the truth.
    Only when there is no matching record (``doctor`` called programmatically, or a different path)
    do we perform the load ourselves; that is a no-op for anything already set.
    """
    recorded = _dotenv.last_load()
    if recorded is not None and Path(recorded.path) == dotenv_path:
        return recorded
    return _dotenv.load_dotenv_report(dotenv_path)


def _settings_report(load: _dotenv.DotenvLoad) -> tuple[list[SettingReport], list[Check]]:
    """Attribute every :data:`SETTINGS` entry to its true source, and flag shadowing."""
    reports: list[SettingReport] = []
    checks: list[Check] = []

    for spec in SETTINGS:
        raw = os.environ.get(spec.name)
        present = raw is not None
        in_dotenv = spec.name in load.keys
        shadowed = load.is_shadowed(spec.name)
        differs = load.shadow_differs(spec.name)

        if not present:
            source = "unset"
        elif load.source_of(spec.name) == "dotenv":
            source = ".env"
        else:
            source = "OS env"

        note = ""
        if not present:
            note = f"default: {spec.default_desc}"
        elif spec.secret and not _looks_like_openrouter_key(raw):
            # Shape only — no characters of the key are echoed.
            note = "shape: does NOT look like an OpenRouter key (expected an 'sk-or-' prefix)"

        reports.append(
            SettingReport(
                name=spec.name,
                present=present,
                source=source,
                value=None if spec.secret else raw,
                length=len(raw) if present else None,
                secret=spec.secret,
                in_dotenv=in_dotenv,
                shadowed=shadowed,
                shadow_differs=differs,
                note=note,
            )
        )

        if shadowed and differs:
            checks.append(
                Check(
                    f"{spec.name} provenance",
                    WARN,
                    f"a DIFFERENT value for {spec.name} is set in the OS environment and is the one "
                    f"in use; the value in {load.path} is never read. Editing the .env will not "
                    "change anything until the OS-environment variable is removed.",
                )
            )
        elif shadowed:
            checks.append(
                Check(
                    f"{spec.name} provenance",
                    OK,
                    f"set in both the OS environment and {load.path}, with the same value "
                    "(the OS environment's is the one in use)",
                )
            )
        elif present:
            checks.append(Check(f"{spec.name} provenance", OK, f"source: {source}"))
        else:
            checks.append(
                Check(
                    f"{spec.name} provenance",
                    WARN if spec.warn_if_absent else OK,
                    f"not set anywhere - {spec.default_desc}",
                )
            )

    return reports, checks


def _looks_like_openrouter_key(value: Optional[str]) -> bool:
    """Shape check only — never reveals any character of ``value``."""
    return bool(value) and value.startswith("sk-or-")


def _dotenv_info(load: _dotenv.DotenvLoad) -> dict:
    """A JSON-safe summary of the `.env` load: names only, never values."""
    return {
        "path": str(load.path),
        "resolved_path": str(Path(load.path).resolve()),
        "exists": load.exists,
        "keys": list(load.keys),
        "loaded": sorted(load.loaded),  # keys this load actually set (names only)
        "shadowed": [
            {"name": k, "differs": load.shadow_differs(k)} for k in sorted(load.shadowed)
        ],
    }


def _model_info(load: _dotenv.DotenvLoad) -> tuple[dict, Check]:
    """The effective model id for the bare ``llm`` agent, and where it came from."""
    default = _default_model()
    env_value = os.environ.get("OPENROUTER_MODEL")
    if env_value:
        effective = env_value
        source = ".env" if load.source_of("OPENROUTER_MODEL") == "dotenv" else "OS env"
    else:
        effective = default
        source = "default (agents/llm.py)"
    info = {
        "effective": effective,
        "source": source,
        "default": default,
        "is_free_tier": effective.endswith(":free"),
    }
    note = "" if info["is_free_tier"] else "  (not a ':free' id - live calls may be billed)"
    return info, Check("llm model", OK, f"{effective} - source: {source}{note}")


# ---------------------------------------------------------------------------------------------
# Fixture provenance (reuses export.py — never reimplemented)
# ---------------------------------------------------------------------------------------------


def _fixture_info(root: Path, seed: int) -> tuple[dict, Check]:
    """Run the existing ``export-profiles --check`` logic and summarise it."""
    from .export import export_profiles

    results = export_profiles(root=root, seed=seed, check=True)
    drift = [r.spec.path for r in results if r.status == "drift"]
    missing = [r.spec.path for r in results if r.status == "missing"]
    info = {
        "checked": True,
        "seed": seed,
        "total": len(results),
        "ok": sum(1 for r in results if r.status == "ok"),
        "drift": drift,
        "missing": missing,
    }
    if drift or missing:
        detail = (
            f"{len(drift)} drifted, {len(missing)} missing of {len(results)} - "
            "run `parkbench export-profiles` to regenerate"
        )
        return info, Check("fixture provenance", FAIL, detail)
    return info, Check(
        "fixture provenance", OK, f"all {len(results)} spectator fixtures match the CLI (seed {seed})"
    )


# ---------------------------------------------------------------------------------------------
# Optional live probe (opt-in; the ONLY code path here that touches the network)
# ---------------------------------------------------------------------------------------------


def _live_probe(seed: int, secrets: tuple[str, ...]) -> tuple[dict, Check]:
    """Make ONE move through the real :class:`LLMAgent` and report live vs. silent fallback.

    Deliberately reuses the production path — ``make_agent("llm")``, the real prompt builder, the
    real ``OpenRouterProvider``, the real parser — so a green result means *a scored run would also
    be live*. A parallel "just ping the API" implementation could pass while real runs still fell
    back (exactly the D-068 failure mode). Exactly one chat completion is requested.
    """
    from .agents import make_agent
    from .agents.llm import LLMAgent
    from .protocol import Observation
    from .scenario import generate_scenario

    agent = make_agent("llm")
    assert isinstance(agent, LLMAgent)  # registry contract; keeps the probe honest
    model = agent.config().get("model")

    if not os.environ.get("OPENROUTER_API_KEY"):
        info = {
            "ran": False,
            "model": model,
            "live_calls": 0,
            "fallback_calls": 0,
            "used_live_llm": False,
            "error": "OPENROUTER_API_KEY is not set",
        }
        return info, Check(
            "live llm probe",
            FAIL,
            "no OPENROUTER_API_KEY - cannot be live; every `--agent llm` run is the heuristic "
            "fallback (no network call was made)",
        )

    sc = generate_scenario(seed)
    obs = Observation(
        role="A",
        my_util=sc.util_table("A"),
        standing_offer=None,
        my_last_offer=None,
        rounds_left=8,
        history=(),
    )
    agent.reset(0, 8)
    agent.act(obs)  # exactly one provider call; LLMAgent never raises (it falls back)

    error = getattr(agent, "last_fallback_error", None)
    info = {
        "ran": True,
        "model": model,
        "live_calls": agent.live_calls,
        "fallback_calls": agent.fallback_calls,
        "used_live_llm": agent.used_live_llm,
        "error": _redact(error, secrets) if error else None,
    }
    if agent.used_live_llm:
        return info, Check(
            "live llm probe", OK, f"live - one call to {model!r} returned a usable move"
        )
    return info, Check(
        "live llm probe",
        FAIL,
        f"NOT live - the call to {model!r} failed and the agent silently fell back to the "
        f"heuristic: {info['error'] or 'unknown error'}",
    )


# ---------------------------------------------------------------------------------------------
# Assembly + rendering
# ---------------------------------------------------------------------------------------------


def build_doctor_report(
    root: Path | str = ".",
    seed: int = 1,
    live: bool = False,
    check_fixtures: bool = True,
    dotenv_path: Path | str = ".env",
) -> DoctorReport:
    """Diagnose the local setup. Makes **no network call** unless ``live=True``."""
    root = Path(root)
    load = _resolve_dotenv_load(Path(dotenv_path))
    secrets = _known_secrets(load)

    report = DoctorReport()
    report.runtime, checks = _runtime_info(root)
    report.dotenv = _dotenv_info(load)
    report.settings, setting_checks = _settings_report(load)
    checks += setting_checks
    report.model, model_check = _model_info(load)
    checks.append(model_check)

    if check_fixtures:
        report.fixtures, fixture_check = _fixture_info(root, seed)
    else:
        report.fixtures = {"checked": False, "seed": seed}
        fixture_check = Check("fixture provenance", SKIP, "skipped (--no-fixtures)")
    checks.append(fixture_check)

    if live:
        report.live, live_check = _live_probe(seed, secrets)
    else:
        report.live = None
        live_check = Check(
            "live llm probe", SKIP, "skipped - pass --live to make one real OpenRouter call"
        )
    checks.append(live_check)

    report.checks = checks
    return report


_SUMMARY = {
    OK: "HEALTHY - no problems found.",
    WARN: "HEALTHY with advisories - see the warnings above (exit 0).",
    FAIL: "PROBLEMS FOUND - see the failures above (exit 1).",
    SKIP: "HEALTHY - no problems found.",
}


def render_doctor_report(report: DoctorReport) -> str:
    """Human-readable, secret-free rendering of a :class:`DoctorReport`."""
    rt = report.runtime
    lines = [f"Parkbench - doctor  (bench v{report.benchmark_version})", ""]

    lines.append("runtime")
    lines.append(f"  python           : {rt['python_implementation']} {rt['python_version']}  ({rt['platform']})")
    lines.append(f"  interpreter      : {rt['executable']}")
    editable = rt["editable_install"]
    kind = "editable" if editable else "non-editable" if editable is False else "not installed as a dist"
    lines.append(f"  parkbench        : {rt['package_version']} ({kind})")
    lines.append(f"  package path     : {rt['package_path']}")
    lines.append(f"  working dir      : {rt['cwd']}")
    lines.append(f"  benchmark version: {rt['benchmark_version']}")
    lines.append("")

    dn = report.dotenv
    found = f"{len(dn['keys'])} key(s)" if dn["exists"] else "not found"
    lines.append(f"config provenance  (.env: {dn['resolved_path']} - {found})")
    for s in report.settings:
        lines.append(f"  {s.name:<20} {s.describe()}")
    lines.append("")

    lines.append("llm model")
    lines.append(f"  effective        : {report.model['effective']}")
    lines.append(f"  source           : {report.model['source']}")
    lines.append(f"  in-code default  : {report.model['default']}")
    lines.append("")

    lines.append("checks")
    width = max((len(c.name) for c in report.checks), default=0)
    for c in report.checks:
        lines.append(f"  [{c.status:<4}] {c.name:<{width}}  {c.detail}")
    lines.append("")
    lines.append(f"  {_SUMMARY[report.status]}")
    return "\n".join(lines)
