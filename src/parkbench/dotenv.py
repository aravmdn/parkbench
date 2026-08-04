"""Minimal, zero-dependency `.env` loader (decision D-033).

The CLI calls :func:`load_dotenv` at startup so a local `.env` in the working
directory (e.g. `OPENROUTER_API_KEY`, `OPENROUTER_MODEL` for the LLM agent) is
picked up automatically — no manual `export` / `$env:` per shell.

**Real environment variables always win:** a key already present in the
environment is never overwritten, so an explicit `export` or a CI secret takes
precedence over the file. A missing file is a silent no-op. Implemented with the
standard library only, to keep the core dependency-free (D-023).

**That precedence is now observable (D-072).** "The OS environment wins" is the right
policy but it used to be *invisible*: a value sitting in `.env` could be silently
shadowed by a different value in the OS environment, and nothing said so — the exact
footgun that cost a session in D-068 (two different `OPENROUTER_API_KEY`s, only the
OS-env one ever used). :func:`load_dotenv_report` therefore returns a
:class:`DotenvLoad` recording **which keys this call actually set** versus **which keys
the file declared but the OS environment already owned**, and the most recent load is
kept in module state for :func:`last_load` so a later consumer (``parkbench doctor``)
can attribute every setting to its true source. Load *semantics* are unchanged:
``load_dotenv`` still never overrides ``os.environ`` and still returns the mapping of
keys it set.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


@dataclass(frozen=True)
class DotenvLoad:
    """What one :func:`load_dotenv_report` call found and did.

    ``loaded`` maps the keys this call **set** into ``os.environ`` (the file value won
    because the variable was absent) to their values. ``shadowed`` maps the keys the file
    declared but whose value was **ignored** because ``os.environ`` already had that
    variable — the OS environment wins (D-033) — to the *file's* (unused) value. ``keys``
    lists every key seen in the file, in file order.

    Values are held only so a caller can compare them (e.g. "is the shadowed value even
    different?"); they are never printed by anything in this package — ``parkbench doctor``
    reports presence, source and length for secrets, never content.
    """

    path: Path
    exists: bool
    loaded: dict[str, str] = field(default_factory=dict)
    shadowed: dict[str, str] = field(default_factory=dict)
    keys: tuple[str, ...] = ()

    def source_of(self, name: str) -> str:
        """Where the *effective* value of ``name`` came from, as far as this load can tell.

        ``"dotenv"`` — this call set it from the file; ``"os-env"`` — it was already in the
        environment (whether or not the file also declares it); ``"absent"`` — not set anywhere.
        """
        if name in self.loaded:
            return "dotenv"
        if name in os.environ:
            return "os-env"
        return "absent"

    def is_shadowed(self, name: str) -> bool:
        """True iff the file declares ``name`` but the OS environment's value is the one in use."""
        return name in self.shadowed

    def shadow_differs(self, name: str) -> bool:
        """True iff ``name`` is shadowed **and** the OS-env value differs from the file's.

        A shadowed-but-identical value is harmless; a shadowed-and-different value means the
        file you are editing is not the thing being used (the D-068 footgun).
        """
        return name in self.shadowed and os.environ.get(name) != self.shadowed[name]


# The most recent load, so a later consumer can attribute sources. The CLI loads the `.env` once at
# startup (``cli.main``), long before any subcommand runs, so by the time ``parkbench doctor`` looks
# at ``os.environ`` a file-sourced value is indistinguishable from an OS-env one; recording the load
# here is what keeps the distinction knowable. ``None`` until the first load.
_LAST_LOAD: Optional[DotenvLoad] = None


def last_load() -> Optional[DotenvLoad]:
    """The :class:`DotenvLoad` from the most recent :func:`load_dotenv` call, or ``None``."""
    return _LAST_LOAD


def parse_dotenv(path: str | os.PathLike[str] = ".env") -> dict[str, str]:
    """Parse ``KEY=VALUE`` lines from ``path`` **without touching** ``os.environ``.

    Lines that are blank, start with ``#``, or lack ``=`` are ignored; an optional leading
    ``export`` and surrounding quotes on the value are stripped. Returns ``{}`` if the file
    is absent. Later duplicate keys overwrite earlier ones (last wins), matching the loader.
    """
    p = Path(path)
    if not p.is_file():
        return {}
    parsed: dict[str, str] = {}
    for raw in p.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        if line.startswith("export "):
            line = line[len("export ") :]
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key:
            parsed[key] = value
    return parsed


def load_dotenv_report(path: str | os.PathLike[str] = ".env") -> DotenvLoad:
    """Load ``path`` into ``os.environ`` and return the full :class:`DotenvLoad` record.

    Identical behaviour to :func:`load_dotenv` (existing environment variables are never
    overwritten); it just also reports what was *not* applied. The result is stored for
    :func:`last_load`.
    """
    global _LAST_LOAD
    p = Path(path)
    parsed = parse_dotenv(p)
    loaded: dict[str, str] = {}
    shadowed: dict[str, str] = {}
    for key, value in parsed.items():
        if key in os.environ:
            shadowed[key] = value  # the OS environment wins (D-033) — file value unused
        else:
            os.environ[key] = value
            loaded[key] = value
    _LAST_LOAD = DotenvLoad(
        path=p,
        exists=p.is_file(),
        loaded=loaded,
        shadowed=shadowed,
        keys=tuple(parsed),
    )
    return _LAST_LOAD


def load_dotenv(path: str | os.PathLike[str] = ".env") -> dict[str, str]:
    """Load ``KEY=VALUE`` lines from ``path`` into ``os.environ``.

    Lines that are blank, start with ``#``, or lack ``=`` are ignored; an
    optional leading ``export`` and surrounding quotes on the value are
    stripped. Existing environment variables are left untouched. Returns the
    mapping of keys this call actually set (empty if the file is absent).

    Thin wrapper over :func:`load_dotenv_report` — use that one when you also need to know
    which keys the file declared but could not apply (see :class:`DotenvLoad`).
    """
    return load_dotenv_report(path).loaded
