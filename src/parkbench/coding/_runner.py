"""The untrusted-candidate runner, executed as a separate process (decision D-043).

This module is the body of the isolated subprocess the harness (`harness.py`) spawns to execute a
candidate's **untrusted** source. It is invoked as ``python -I -m parkbench.coding._runner`` (isolated
mode) and speaks a tiny, one-shot, text-only protocol so the parent never has to trust anything that
crosses the process boundary:

  - **In (stdin):** one JSON object ``{"source": str, "entry_point": str, "inputs": [[args...], ...]}``.
    Inputs are passed via stdin (not argv, not a predictable temp path) so a hostile candidate can't
    read them out of the process table or a guessable file.
  - **Out (stdout):** one JSON object ``{"results": [[ok, type_name, value_repr], ...]}`` — one entry
    per input, in order. ``ok`` is whether the candidate returned (vs. raised); ``type_name`` is
    ``type(value).__name__`` and ``value_repr`` is ``repr(value)``. We emit *text* (a name + a repr),
    **never a pickle**, precisely because the parent must not unpickle untrusted output (that would be
    its own RCE vector). The parent reconstructs the strict value+type comparison from these.

Only the candidate function is untrusted; this wrapper is our code. It is deliberately tiny and
total: any per-call exception is caught and reported as ``ok = False`` so one bad input never aborts
the batch, and a candidate that fails to compile / lacks the entry point makes the *whole* run report
a structured failure (non-zero exit), which the parent treats as "every test failed".
"""

from __future__ import annotations

import json
import sys


def _emit(obj: dict) -> None:
    sys.stdout.write(json.dumps(obj))
    sys.stdout.flush()


def main() -> int:
    try:
        payload = json.loads(sys.stdin.read())
        source = payload["source"]
        entry_point = payload["entry_point"]
        inputs = payload["inputs"]
    except Exception:
        # Unparseable request: nothing we can score. The parent reads exit!=0 as "all fail".
        return 2

    namespace: dict = {}
    try:
        compiled = compile(source, f"<candidate:{entry_point}>", "exec")
        exec(compiled, namespace)  # noqa: S102 - this is the whole point: run untrusted candidate code
    except BaseException:
        # Does not compile / blows up at import time -> candidate didn't even define a function.
        return 3

    fn = namespace.get(entry_point)
    if not callable(fn):
        return 4

    results: list = []
    for args in inputs:
        try:
            value = fn(*args)
            # repr() can itself raise on a hostile __repr__; treat that as a failed call.
            results.append([True, type(value).__name__, repr(value)])
        except BaseException:
            results.append([False, None, None])

    _emit({"results": results})
    return 0


if __name__ == "__main__":
    sys.exit(main())
