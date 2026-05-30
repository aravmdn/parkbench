"""Tests for the zero-dependency .env loader (D-033)."""

from __future__ import annotations

import os

from parkbench.dotenv import load_dotenv


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
