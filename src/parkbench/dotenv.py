"""Minimal, zero-dependency `.env` loader (decision D-033).

The CLI calls :func:`load_dotenv` at startup so a local `.env` in the working
directory (e.g. `OPENROUTER_API_KEY`, `OPENROUTER_MODEL` for the LLM agent) is
picked up automatically — no manual `export` / `$env:` per shell.

**Real environment variables always win:** a key already present in the
environment is never overwritten, so an explicit `export` or a CI secret takes
precedence over the file. A missing file is a silent no-op. Implemented with the
standard library only, to keep the core dependency-free (D-023).
"""

from __future__ import annotations

import os
from pathlib import Path


def load_dotenv(path: str | os.PathLike[str] = ".env") -> dict[str, str]:
    """Load ``KEY=VALUE`` lines from ``path`` into ``os.environ``.

    Lines that are blank, start with ``#``, or lack ``=`` are ignored; an
    optional leading ``export`` and surrounding quotes on the value are
    stripped. Existing environment variables are left untouched. Returns the
    mapping of keys this call actually set (empty if the file is absent).
    """
    p = Path(path)
    if not p.is_file():
        return {}
    loaded: dict[str, str] = {}
    for raw in p.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        if line.startswith("export "):
            line = line[len("export ") :]
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value
            loaded[key] = value
    return loaded
