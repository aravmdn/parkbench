"""Tests for ``parkbench doctor`` — the setup diagnosis + config-provenance report (D-072).

Everything here runs **offline**: the only code path that can touch the network is the opt-in
``--live`` probe, and it is exercised with a stubbed provider (never a real call). Several tests
install a tripwire over ``urllib.request.urlopen`` so a regression that starts calling out is caught
rather than silently making the suite depend on a key.

The headline behaviour under test is the D-068 footgun: a value in `.env` that is silently shadowed
by a *different* value in the OS environment must be reported, and the secret's content must never
appear in the text report or the ``--json`` payload.
"""

from __future__ import annotations

import json

import pytest

from parkbench import BENCHMARK_VERSION, cli, doctor
from parkbench.agents.llm import OpenRouterProvider
from parkbench.dotenv import load_dotenv_report
from parkbench.export import FixtureResult, FixtureSpec

KEY = "OPENROUTER_API_KEY"
MODEL = "OPENROUTER_MODEL"

# Distinctive dummy values — never a real key. Long enough to be recognisable in any leak.
OS_KEY = "sk-or-DUMMY-OS-ENVIRONMENT-VALUE-0123456789"
FILE_KEY = "sk-or-DUMMY-DOTENV-FILE-VALUE-9876543210"


def _no_network(monkeypatch):
    """Trip the test if anything in the report path opens a socket."""

    def _boom(*a, **k):  # pragma: no cover - only runs on a regression
        raise AssertionError("doctor made a network call")

    monkeypatch.setattr("urllib.request.urlopen", _boom)


def _write_env(tmp_path, text):
    p = tmp_path / ".env"
    p.write_text(text, encoding="utf-8")
    return p


def _clean_env(monkeypatch):
    """Detach both settings from the ambient machine so tests are deterministic.

    ``monkeypatch.delenv`` registers each name for restoration, so anything ``load_dotenv``
    subsequently sets is undone at teardown too.
    """
    monkeypatch.delenv(KEY, raising=False)
    monkeypatch.delenv(MODEL, raising=False)


def _report(tmp_path, **kw):
    """Build a report pinned to a temp `.env`, with the slow fixture check off by default."""
    kw.setdefault("check_fixtures", False)
    kw.setdefault("dotenv_path", tmp_path / ".env")
    return doctor.build_doctor_report(root=tmp_path, **kw)


def _check(report, name):
    for c in report.checks:
        if c.name == name:
            return c
    raise AssertionError(f"no check named {name!r} in {[c.name for c in report.checks]}")


def _setting(report, name):
    for s in report.settings:
        if s.name == name:
            return s
    raise AssertionError(f"no setting named {name!r}")


# ------------------------------------------------------------------------------------------------
# Runtime
# ------------------------------------------------------------------------------------------------


def test_runtime_section_describes_this_interpreter_and_version(tmp_path, monkeypatch):
    _clean_env(monkeypatch)
    _no_network(monkeypatch)
    rt = _report(tmp_path).runtime
    assert rt["benchmark_version"] == BENCHMARK_VERSION
    assert rt["python_version"].count(".") == 2
    assert rt["package_path"].endswith("parkbench")
    # Editability is either known (bool) or honestly reported as unknown.
    assert rt["editable_install"] in (True, False, None)


def test_report_is_offline_and_healthy_by_default(tmp_path, monkeypatch):
    """No `--live` => zero network calls, and an unset optional setting is not a failure."""
    _clean_env(monkeypatch)
    _no_network(monkeypatch)
    report = _report(tmp_path)
    assert report.live is None
    assert _check(report, "live llm probe").status == doctor.SKIP
    assert report.exit_code == 0


# ------------------------------------------------------------------------------------------------
# Config provenance — the headline
# ------------------------------------------------------------------------------------------------


def test_os_env_shadowing_a_different_dotenv_value_is_reported(tmp_path, monkeypatch):
    """THE D-068 case: two different keys, the OS environment's wins, and doctor says so."""
    _clean_env(monkeypatch)
    _no_network(monkeypatch)
    monkeypatch.setenv(KEY, OS_KEY)
    env_file = _write_env(tmp_path, f"{KEY}={FILE_KEY}\n")
    load_dotenv_report(env_file)  # what the CLI does at startup

    report = _report(tmp_path)
    s = _setting(report, KEY)
    assert s.present and s.source == "OS env"
    assert s.in_dotenv and s.shadowed and s.shadow_differs
    assert s.length == len(OS_KEY)  # length of the EFFECTIVE value
    assert s.value is None  # secrets never carry content

    c = _check(report, f"{KEY} provenance")
    assert c.status == doctor.WARN
    assert "DIFFERENT value" in c.detail
    # Advisory, not broken: the command still exits 0.
    assert report.exit_code == 0
    assert report.status == doctor.WARN


def test_shadowing_with_an_identical_value_is_not_a_warning(tmp_path, monkeypatch):
    _clean_env(monkeypatch)
    _no_network(monkeypatch)
    monkeypatch.setenv(KEY, OS_KEY)
    load_dotenv_report(_write_env(tmp_path, f"{KEY}={OS_KEY}\n"))

    report = _report(tmp_path)
    s = _setting(report, KEY)
    assert s.shadowed and not s.shadow_differs
    assert _check(report, f"{KEY} provenance").status == doctor.OK


def test_dotenv_sourced_value_is_attributed_to_the_file(tmp_path, monkeypatch):
    _clean_env(monkeypatch)
    _no_network(monkeypatch)
    load_dotenv_report(_write_env(tmp_path, f"{KEY}={FILE_KEY}\n{MODEL}=vendor/from-file:free\n"))

    report = _report(tmp_path)
    key = _setting(report, KEY)
    assert key.present and key.source == ".env" and not key.shadowed
    assert key.length == len(FILE_KEY) and key.value is None
    model = _setting(report, MODEL)
    assert model.source == ".env" and model.value == "vendor/from-file:free"  # not a secret


def test_absent_key_warns_but_absent_optional_setting_does_not(tmp_path, monkeypatch):
    _clean_env(monkeypatch)
    _no_network(monkeypatch)
    report = _report(tmp_path)
    assert _setting(report, KEY).source == "unset"
    assert _check(report, f"{KEY} provenance").status == doctor.WARN
    # OPENROUTER_MODEL falls back to a documented in-code default — that is normal, not an advisory.
    assert _check(report, f"{MODEL} provenance").status == doctor.OK
    assert report.exit_code == 0


def test_dotenv_summary_lists_names_only(tmp_path, monkeypatch):
    _clean_env(monkeypatch)
    _no_network(monkeypatch)
    load_dotenv_report(_write_env(tmp_path, f"{KEY}={FILE_KEY}\n"))
    dn = _report(tmp_path).dotenv
    assert dn["exists"] is True
    assert dn["keys"] == [KEY] and dn["loaded"] == [KEY]
    assert FILE_KEY not in json.dumps(dn)


def test_missing_dotenv_file_is_reported_not_an_error(tmp_path, monkeypatch):
    _clean_env(monkeypatch)
    _no_network(monkeypatch)
    report = _report(tmp_path)
    assert report.dotenv["exists"] is False
    assert report.exit_code == 0


def test_unexpected_key_shape_is_noted_without_echoing_the_value(tmp_path, monkeypatch):
    _clean_env(monkeypatch)
    _no_network(monkeypatch)
    monkeypatch.setenv(KEY, "definitely-not-an-openrouter-key")
    report = _report(tmp_path)
    s = _setting(report, KEY)
    assert "sk-or-" in s.note  # tells you the expected shape...
    assert "definitely-not" not in doctor.render_doctor_report(report)  # ...never yours


# ------------------------------------------------------------------------------------------------
# Secrets hygiene
# ------------------------------------------------------------------------------------------------


@pytest.mark.parametrize("live", [False, True])
def test_secret_never_appears_in_text_or_json(tmp_path, monkeypatch, live, capsys):
    _clean_env(monkeypatch)
    monkeypatch.setenv(KEY, OS_KEY)
    load_dotenv_report(_write_env(tmp_path, f"{KEY}={FILE_KEY}\n"))
    # The live path is stubbed to fail with a message that (hostilely) embeds both secrets.
    monkeypatch.setattr(
        OpenRouterProvider,
        "complete",
        lambda self, messages, **o: (_ for _ in ()).throw(
            RuntimeError(f"HTTP 401 for key {OS_KEY} / {FILE_KEY}")
        ),
    )
    report = _report(tmp_path, live=live)

    text = doctor.render_doctor_report(report)
    payload = json.dumps(report.to_dict())
    for secret in (OS_KEY, FILE_KEY):
        assert secret not in text
        assert secret not in payload
    capsys.readouterr()  # swallow the agent's one-time stderr fallback notice


def test_redact_scrubs_every_known_secret():
    assert doctor._redact("before abc middle def after", ("abc", "def")) == (
        f"before {doctor.REDACTED} middle {doctor.REDACTED} after"
    )
    assert doctor._redact("nothing to do", ("",)) == "nothing to do"


# ------------------------------------------------------------------------------------------------
# Model resolution
# ------------------------------------------------------------------------------------------------


def test_model_falls_back_to_the_in_code_default(tmp_path, monkeypatch):
    from parkbench.agents.llm import DEFAULT_MODEL

    _clean_env(monkeypatch)
    _no_network(monkeypatch)
    m = _report(tmp_path).model
    assert m["effective"] == DEFAULT_MODEL == m["default"]
    assert m["source"].startswith("default")
    assert m["is_free_tier"] is True


def test_model_override_source_is_reported(tmp_path, monkeypatch):
    _clean_env(monkeypatch)
    _no_network(monkeypatch)
    monkeypatch.setenv(MODEL, "vendor/paid-model")
    m = _report(tmp_path).model
    assert m["effective"] == "vendor/paid-model"
    assert m["source"] == "OS env"
    assert m["is_free_tier"] is False


# ------------------------------------------------------------------------------------------------
# Fixture provenance — must REUSE export.py, never reimplement it
# ------------------------------------------------------------------------------------------------


def _stub_export(monkeypatch, statuses):
    """Replace ``export.export_profiles`` with a stub; return the recorded call kwargs."""
    seen: dict = {}

    def _fake(root, seed, check):
        seen.update(root=root, seed=seed, check=check)
        return [
            FixtureResult(FixtureSpec(f"f{i}.json", "radar", "heuristic"), st)
            for i, st in enumerate(statuses)
        ]

    monkeypatch.setattr("parkbench.export.export_profiles", _fake)
    return seen


def test_fixture_check_delegates_to_export_profiles(tmp_path, monkeypatch):
    _clean_env(monkeypatch)
    _no_network(monkeypatch)
    seen = _stub_export(monkeypatch, ["ok", "ok"])
    report = _report(tmp_path, check_fixtures=True, seed=7)
    assert seen == {"root": tmp_path, "seed": 7, "check": True}  # the real --check logic, reused
    assert report.fixtures["ok"] == 2 and report.fixtures["total"] == 2
    assert _check(report, "fixture provenance").status == doctor.OK
    assert report.exit_code == 0


def test_fixture_drift_is_a_failure_with_exit_code_1(tmp_path, monkeypatch):
    _clean_env(monkeypatch)
    _no_network(monkeypatch)
    _stub_export(monkeypatch, ["ok", "drift", "missing"])
    report = _report(tmp_path, check_fixtures=True)
    assert report.fixtures["drift"] and report.fixtures["missing"]
    assert _check(report, "fixture provenance").status == doctor.FAIL
    assert report.status == doctor.FAIL and report.exit_code == 1


def test_fixture_check_can_be_skipped(tmp_path, monkeypatch):
    _clean_env(monkeypatch)
    _no_network(monkeypatch)
    report = _report(tmp_path, check_fixtures=False)
    assert report.fixtures["checked"] is False
    assert _check(report, "fixture provenance").status == doctor.SKIP


# ------------------------------------------------------------------------------------------------
# The opt-in live probe (stubbed — never a real call)
# ------------------------------------------------------------------------------------------------


def test_live_probe_reports_a_genuinely_live_agent(tmp_path, monkeypatch):
    _clean_env(monkeypatch)
    monkeypatch.setenv(KEY, OS_KEY)
    reply = json.dumps({"type": "message", "message": "hi"})
    monkeypatch.setattr(OpenRouterProvider, "complete", lambda self, messages, **o: reply)

    report = _report(tmp_path, live=True)
    assert report.live["ran"] is True
    assert report.live["used_live_llm"] is True
    assert report.live["live_calls"] == 1 and report.live["fallback_calls"] == 0
    assert _check(report, "live llm probe").status == doctor.OK
    assert report.exit_code == 0


def test_live_probe_catches_a_silent_fallback(tmp_path, monkeypatch, capsys):
    """The D-068 symptom: a key IS set but the call fails and the agent quietly plays heuristic."""
    _clean_env(monkeypatch)
    monkeypatch.setenv(KEY, OS_KEY)

    def _boom(self, messages, **o):
        raise RuntimeError("HTTP Error 404: model not found")

    monkeypatch.setattr(OpenRouterProvider, "complete", _boom)

    report = _report(tmp_path, live=True)
    assert report.live["used_live_llm"] is False
    assert report.live["fallback_calls"] == 1
    assert "404" in report.live["error"]  # the reason, not just "it didn't work"
    c = _check(report, "live llm probe")
    assert c.status == doctor.FAIL and "NOT live" in c.detail
    assert report.exit_code == 1
    capsys.readouterr()


def test_live_probe_without_a_key_fails_without_touching_the_network(tmp_path, monkeypatch):
    _clean_env(monkeypatch)
    _no_network(monkeypatch)  # tripwire: a keyless probe must not even try
    report = _report(tmp_path, live=True)
    assert report.live["ran"] is False
    assert report.live["used_live_llm"] is False
    assert _check(report, "live llm probe").status == doctor.FAIL
    assert report.exit_code == 1


def test_live_probe_makes_exactly_one_call(tmp_path, monkeypatch):
    _clean_env(monkeypatch)
    monkeypatch.setenv(KEY, OS_KEY)
    calls = []
    reply = json.dumps({"type": "message", "message": "hi"})

    def _record(self, messages, **o):
        calls.append(messages)
        return reply

    monkeypatch.setattr(OpenRouterProvider, "complete", _record)
    _report(tmp_path, live=True)
    assert len(calls) == 1  # "cheap" means one completion, not a whole match


# ------------------------------------------------------------------------------------------------
# CLI surface
# ------------------------------------------------------------------------------------------------


def test_cli_doctor_runs_and_exits_zero(tmp_path, monkeypatch, capsys):
    _clean_env(monkeypatch)
    _no_network(monkeypatch)
    monkeypatch.chdir(tmp_path)
    code = cli.main(["doctor", "--no-fixtures"])
    out = capsys.readouterr().out
    assert code == 0
    assert "Parkbench - doctor" in out
    assert "config provenance" in out


def test_cli_doctor_json_is_stamped_like_every_other_json_command(tmp_path, monkeypatch, capsys):
    _clean_env(monkeypatch)
    _no_network(monkeypatch)
    monkeypatch.chdir(tmp_path)
    code = cli.main(["doctor", "--no-fixtures", "--json"])
    payload = json.loads(capsys.readouterr().out)
    assert code == 0
    # D-061: benchmark_version is the first key of every CLI --json result.
    assert next(iter(payload)) == "benchmark_version"
    assert payload["benchmark_version"] == BENCHMARK_VERSION
    for key in ("runtime", "dotenv", "settings", "model", "fixtures", "live", "checks", "status"):
        assert key in payload
    assert payload["live"] is None  # no --live => no probe


def test_cli_doctor_reports_shadowing_end_to_end(tmp_path, monkeypatch, capsys):
    """From the shell, in the exact shape that would have saved the D-068 session."""
    _clean_env(monkeypatch)
    _no_network(monkeypatch)
    monkeypatch.setenv(KEY, OS_KEY)
    _write_env(tmp_path, f"{KEY}={FILE_KEY}\n")
    monkeypatch.chdir(tmp_path)  # cli.main loads ./.env at startup

    code = cli.main(["doctor", "--no-fixtures"])
    out = capsys.readouterr().out
    assert code == 0
    assert "SHADOWED" in out
    assert "source: OS env" in out
    assert OS_KEY not in out and FILE_KEY not in out


def test_cli_doctor_exit_code_1_on_fixture_drift(tmp_path, monkeypatch, capsys):
    _clean_env(monkeypatch)
    _no_network(monkeypatch)
    _stub_export(monkeypatch, ["drift"])
    monkeypatch.chdir(tmp_path)
    assert cli.main(["doctor"]) == 1
    assert "PROBLEMS FOUND" in capsys.readouterr().out
