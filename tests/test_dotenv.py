"""Tests for the zero-dependency .env loader (D-033) and its load record (D-072)."""

from __future__ import annotations

import os

from parkbench.dotenv import last_load, load_dotenv, load_dotenv_report, parse_dotenv


def _write(tmp_path, text):
    p = tmp_path / ".env"
    p.write_text(text, encoding="utf-8")
    return p


def test_missing_file_is_noop(tmp_path):
    assert load_dotenv(tmp_path / "nope.env") == {}


def test_loads_keys_and_strips_quotes_and_export(tmp_path, monkeypatch):
    monkeypatch.delenv("PB_A", raising=False)
    monkeypatch.delenv("PB_B", raising=False)
    monkeypatch.delenv("PB_C", raising=False)
    p = _write(
        tmp_path,
        "# a comment\n\nPB_A=plain\nPB_B=\"quoted\"\nexport PB_C='exported'\nnot_a_pair\n",
    )
    loaded = load_dotenv(p)
    assert loaded == {"PB_A": "plain", "PB_B": "quoted", "PB_C": "exported"}
    assert os.environ["PB_A"] == "plain"
    assert os.environ["PB_B"] == "quoted"
    assert os.environ["PB_C"] == "exported"


def test_does_not_override_existing_env(tmp_path, monkeypatch):
    monkeypatch.setenv("PB_EXISTING", "from-env")
    p = _write(tmp_path, "PB_EXISTING=from-file\n")
    loaded = load_dotenv(p)
    assert loaded == {}  # nothing set
    assert os.environ["PB_EXISTING"] == "from-env"  # real env var wins


# ---------------------------------------------------------------------------------------------
# The load record (D-072): the OS-env-wins precedence must be OBSERVABLE, not just correct.
# ---------------------------------------------------------------------------------------------


def test_parse_does_not_touch_the_environment(tmp_path, monkeypatch):
    monkeypatch.delenv("PB_PARSE", raising=False)
    parsed = parse_dotenv(_write(tmp_path, "PB_PARSE=value\n"))
    assert parsed == {"PB_PARSE": "value"}
    assert "PB_PARSE" not in os.environ  # inspection only


def test_parse_missing_file_is_empty(tmp_path):
    assert parse_dotenv(tmp_path / "nope.env") == {}


def test_report_separates_loaded_from_shadowed(tmp_path, monkeypatch):
    monkeypatch.setenv("PB_SHADOWED", "from-env")
    monkeypatch.delenv("PB_FRESH", raising=False)
    p = _write(tmp_path, "PB_SHADOWED=from-file\nPB_FRESH=from-file\n")

    rep = load_dotenv_report(p)
    assert rep.exists is True
    assert rep.keys == ("PB_SHADOWED", "PB_FRESH")
    assert rep.loaded == {"PB_FRESH": "from-file"}  # only this one was applied
    assert rep.shadowed == {"PB_SHADOWED": "from-file"}  # this file value is never used
    assert os.environ["PB_SHADOWED"] == "from-env"
    assert os.environ["PB_FRESH"] == "from-file"


def test_source_of_and_shadow_flags(tmp_path, monkeypatch):
    monkeypatch.setenv("PB_SHADOWED", "from-env")
    monkeypatch.setenv("PB_SAME", "same-value")
    monkeypatch.delenv("PB_FRESH", raising=False)
    monkeypatch.delenv("PB_NOWHERE", raising=False)
    rep = load_dotenv_report(
        _write(tmp_path, "PB_SHADOWED=from-file\nPB_SAME=same-value\nPB_FRESH=from-file\n")
    )

    assert rep.source_of("PB_FRESH") == "dotenv"
    assert rep.source_of("PB_SHADOWED") == "os-env"
    assert rep.source_of("PB_NOWHERE") == "absent"

    # Shadowed AND different is the footgun; shadowed with the same value is harmless.
    assert rep.is_shadowed("PB_SHADOWED") and rep.shadow_differs("PB_SHADOWED")
    assert rep.is_shadowed("PB_SAME") and not rep.shadow_differs("PB_SAME")
    assert not rep.is_shadowed("PB_FRESH") and not rep.shadow_differs("PB_FRESH")


def test_report_for_a_missing_file(tmp_path):
    rep = load_dotenv_report(tmp_path / "nope.env")
    assert rep.exists is False
    assert rep.loaded == {} and rep.shadowed == {} and rep.keys == ()


def test_last_load_records_the_most_recent_load(tmp_path, monkeypatch):
    monkeypatch.delenv("PB_LAST", raising=False)
    p = _write(tmp_path, "PB_LAST=value\n")
    load_dotenv(p)  # the plain loader records too
    rep = last_load()
    assert rep is not None
    assert rep.loaded == {"PB_LAST": "value"}
    assert str(rep.path) == str(p)


def test_load_dotenv_return_value_is_unchanged(tmp_path, monkeypatch):
    """The wrapper's contract (keys actually set) must not drift — callers depend on it."""
    monkeypatch.delenv("PB_W1", raising=False)
    monkeypatch.setenv("PB_W2", "from-env")
    assert load_dotenv(_write(tmp_path, "PB_W1=a\nPB_W2=b\n")) == {"PB_W1": "a"}
