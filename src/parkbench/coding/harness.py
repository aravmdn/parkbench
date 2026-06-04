"""The hidden-test harness for the coding ride (decisions D-039, D-043).

The harness is the genuinely reusable, gaming-resistant core: it takes a task, a candidate's
**source code**, and a seed, and returns the fraction of hidden tests the candidate passes. It is
the same machinery whether the source came from a baseline or a real code-writing agent.

How a task is graded for a given seed:
  1. Generate `n_tests` input tuples deterministically from the seed (`task.gen_inputs`).
  2. Compute each *expected* output by running the task's **reference** solution (the oracle).
  3. Run the candidate source in an **isolated subprocess** (D-043) on all `n_tests` inputs at once.
  4. Score = (# candidate outputs that strictly match the oracle's) / n_tests.

Isolation & robustness (D-043): the candidate is **untrusted**, so it runs in a separate Python
process (`sys.executable -I`, isolated mode) under a wall-clock `timeout`. A candidate that
infinite-loops, hangs, crashes, exits non-zero, or emits unparseable output simply **fails** the
affected tests (score 0) — it never hangs or crashes the ride/suite (the child is killed on timeout).
The trusted in-repo **oracle stays in-process** (only the candidate is untrusted). The candidate
source + per-test inputs are handed to the child over **stdin as JSON** (never argv or a predictable
temp path), and the child returns **text only** — `(ok, type_name, repr(value))` per test — which the
parent never unpickles (unpickling untrusted output would be its own RCE vector); see
``parkbench.coding._runner``.

The strict value+type match (D-039) is preserved across the process boundary: a test passes iff the
child reported a successful call **and** `type_name == type(expected).__name__` **and**
`repr(value) == repr(expected)` (so e.g. a `bool` task isn't passed by returning 1/0). reprs are
compared between the parent and a child running the *same* `sys.executable`, so they agree.

Isolation also covers the **environment and the working directory** (D-048): the child gets a minimal,
allowlisted environment (so untrusted code can't read parent secrets out of ``os.environ``) and runs
in a fresh throwaway directory that is deleted afterwards (so a relative file write lands in a sandbox,
not the repo). See ``_child_env`` / ``_run_candidate``.

Known limitation (honest scope): this is **process isolation + a wall-clock timeout + environment and
cwd confinement**, not a full OS sandbox — the child still has **network access**, can reach the
filesystem by **absolute path**, runs with the parent's OS privileges, and has **no CPU/memory/output
caps**. Confining those (filesystem/network jails, resource limits, an OS sandbox or container) is the
remaining BYO-hardening work tracked in ``docs/04-open-questions.md``.
"""

from __future__ import annotations

import json
import os
import random
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass

from .tasks import CodingTask

DEFAULT_N_TESTS = 8
DEFAULT_TIMEOUT = 5.0  # seconds of wall-clock for one task's whole subprocess (all n_tests inputs)

# Environment confinement (D-048). `-I` already makes the child ignore PYTHON* config vars, user
# site-packages, and the cwd — but the spawned process still *inherits the parent's whole
# environment*, so untrusted candidate code could read secrets out of `os.environ` (e.g. an
# `OPENROUTER_API_KEY` loaded by the CLI, D-033). We therefore hand the child a **minimal,
# allowlisted** environment: only the variables an interpreter needs to start. It is an allowlist (not
# a denylist) on purpose — a new secret in the parent env is dropped by default, never leaked. PATH is
# included so the OS can resolve shared libs; the rest are the Windows/POSIX bootstrap essentials.
_ENV_ALLOWLIST = (
    "PATH", "PATHEXT", "COMSPEC",  # process/lib resolution
    "SYSTEMROOT", "SYSTEMDRIVE", "WINDIR",  # Windows interpreter bootstrap
    "TEMP", "TMP", "TMPDIR",  # temp dir for the child's own use
    "LANG", "LC_ALL", "LC_CTYPE",  # locale (avoids spurious encoding differences)
)


def _child_env() -> dict:
    """Build the minimal, allowlisted environment for the untrusted child (D-048).

    Copies only the bootstrap variables in ``_ENV_ALLOWLIST`` from the parent; everything else
    (including any secrets) is omitted, so a hostile candidate reading ``os.environ`` finds nothing
    sensitive. ``PYTHONDONTWRITEBYTECODE`` is set so the child cannot scatter ``__pycache__`` into its
    sandbox dir.
    """
    env = {k: os.environ[k] for k in _ENV_ALLOWLIST if k in os.environ}
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    return env


@dataclass(frozen=True)
class TaskResult:
    """One task's grade for one candidate: how many of its hidden tests passed."""

    task: str
    difficulty: int
    passed: int
    total: int
    compiled: bool  # did the candidate source compile and expose the entry point (in the subprocess)?

    @property
    def score(self) -> float:
        return self.passed / self.total if self.total else 0.0


def _load_entry_point(source: str, entry_point: str):
    """Compile *trusted* `source` in a fresh namespace and return its `entry_point` callable.

    Used **only for the in-repo oracle** (the reference solution), which is trusted. Untrusted
    candidate source is never run this way — it goes through the subprocess runner. Returns ``None``
    if the source does not compile/exec or does not define a callable of that name.
    """
    if not isinstance(source, str):
        return None
    namespace: dict = {}
    try:
        compiled = compile(source, f"<oracle:{entry_point}>", "exec")
        exec(compiled, namespace)  # noqa: S102 - trusted in-repo reference oracle only
    except Exception:
        return None
    fn = namespace.get(entry_point)
    return fn if callable(fn) else None


def _run_candidate(source: str, entry_point: str, inputs: list, timeout: float) -> list | None:
    """Run untrusted `source` over `inputs` in an isolated subprocess (D-043).

    Returns a list of ``[ok, type_name, value_repr]`` rows (one per input) on success, or ``None`` if
    the candidate did not compile, lacked the entry point, hung/timed out, crashed, exited non-zero,
    or produced unparseable output. ``None`` means "every test fails" — never an exception.
    """
    if not isinstance(source, str):
        return None
    request = json.dumps({"source": source, "entry_point": entry_point, "inputs": inputs})
    # Run the child in a fresh throwaway directory (D-048) so any relative file the candidate writes
    # lands in a sandbox dir we delete, not in the repo / caller's cwd. `-m parkbench.coding._runner`
    # still resolves via the installed package on sys.path (not the cwd), so the change is safe.
    sandbox = tempfile.mkdtemp(prefix="parkbench-cand-")
    try:
        # `-I` = isolated mode: ignore env vars (PYTHON*), user site-packages, and the cwd on sys.path,
        # so the child can't be steered by ambient state. We still inherit the parent's interpreter
        # (`sys.executable`) so reprs match exactly. `env=`/`cwd=` add environment + filesystem-cwd
        # confinement (D-048): a minimal allowlisted env (no inherited secrets) and a sandbox cwd.
        proc = subprocess.run(
            [sys.executable, "-I", "-m", "parkbench.coding._runner"],
            input=request,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=sandbox,
            env=_child_env(),
        )
    except subprocess.TimeoutExpired:
        # `subprocess.run` already terminates (kills) the child before raising; nothing leaks.
        return None
    except Exception:  # pragma: no cover - spawn failure (e.g. interpreter missing) -> all fail
        return None
    finally:
        shutil.rmtree(sandbox, ignore_errors=True)

    if proc.returncode != 0:
        # Non-zero = didn't compile / no entry point / crashed / unparseable request: all tests fail.
        return None
    try:
        payload = json.loads(proc.stdout)
        results = payload["results"]
    except Exception:
        return None
    if not isinstance(results, list) or len(results) != len(inputs):
        return None
    return results


def grade(
    task: CodingTask,
    source: str,
    seed: int,
    n_tests: int = DEFAULT_N_TESTS,
    timeout: float = DEFAULT_TIMEOUT,
) -> TaskResult:
    """Grade candidate `source` for `task` over `n_tests` seeded hidden tests.

    Deterministic in `seed`: the same seed yields the same inputs and the same expected outputs
    (computed via the in-process reference oracle). The untrusted candidate runs in an isolated
    subprocess bounded by `timeout` seconds (D-043); a candidate that hangs, crashes, or returns the
    wrong value/type counts as a fail for the affected tests and never crashes the ride.
    """
    oracle = _load_entry_point(task.reference, task.entry_point)
    if oracle is None:  # pragma: no cover - guards against a malformed reference at authoring time
        raise ValueError(f"task '{task.name}' has a broken reference solution")

    # Inputs are drawn from a seed mixed with the task name, so different tasks get independent
    # streams while the whole suite stays reproducible for a given suite seed.
    rng = random.Random(f"{seed}:{task.name}")
    inputs: list[list] = []
    expected: list = []
    for _ in range(n_tests):
        args = task.gen_inputs(rng)
        expected.append(oracle(*args))  # the oracle is trusted, so this is not guarded
        # JSON has no tuple; the runner calls fn(*args), so a list of positional args is equivalent.
        inputs.append(list(args))

    results = _run_candidate(source, task.entry_point, inputs, timeout)
    compiled = results is not None

    passed = 0
    if results is not None:
        for exp, row in zip(expected, results):
            ok, type_name, value_repr = row
            # Strict match (value *and* type), reconstructed from the child's text-only report so a
            # bool task isn't passed by returning 1/0. reprs match because parent and child share the
            # same interpreter (`sys.executable`).
            if ok and type_name == type(exp).__name__ and value_repr == repr(exp):
                passed += 1

    return TaskResult(
        task=task.name,
        difficulty=int(task.difficulty),
        passed=passed,
        total=n_tests,
        compiled=compiled,
    )
