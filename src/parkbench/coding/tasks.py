"""The curated coding-task suite + seeded test generators (decision D-039).

The coding ride is the project's third ride and the first on the **coding** axis (D-005). It is a
clean *solo* ride (D-006): an agent is handed a small, self-contained programming task and must emit
**source code** for the task's entry-point function; a hidden test harness then runs that function
and grades it on an objective pass rate. Same backbone as the other rides — objective payoff vs.
baselines (D-011/D-019), normalized to ``[0, 1]`` (D-035).

Two design choices keep this rigorous and gaming-resistant:

  - **The reference solution is the oracle.** Each `CodingTask` ships one correct implementation.
    For a given seed the harness generates inputs, computes the *expected* output by running the
    reference on those inputs, then compares the candidate's output. So authoring a task means
    writing exactly one correct function + an input generator — the expected answers are never
    hand-listed and can never drift.
  - **Seed-randomized hidden tests.** Inputs are drawn from the suite seed, not fixed constants, so
    an agent cannot pass by memorizing input→output pairs — it must implement real logic. This
    directly blunts the "reward-hacking by memorization" failure mode (see
    ``docs/04-open-questions.md``) while leaving `optimal` at 1.0 by construction.

Tasks are tagged with a `Difficulty` tier; the baseline agents (`coding/agents.py`) solve up to a
capability ceiling, which calibrates the ``[0, 1]`` scale with a clean monotone gradient
(optimal > heuristic > greedy > random). The harness grades whatever source an agent emits
*identically*, so a genuine code-writing agent (an LLM/BYO agent) is scored by the exact same
machinery.
"""

from __future__ import annotations

import random
from dataclasses import dataclass
from enum import IntEnum
from typing import Callable


class Difficulty(IntEnum):
    """Capability tiers, ordered so a baseline can solve "up to" a ceiling (agents.py)."""

    EASY = 1
    MEDIUM = 2
    HARD = 3


# A single hidden test: positional args for the entry point + the expected return value.
TestCase = tuple[tuple, object]


@dataclass(frozen=True)
class CodingTask:
    """One self-contained programming task.

    - ``entry_point`` is the function name the candidate source must define.
    - ``reference`` is correct source defining ``entry_point``; it doubles as the **oracle** that
      computes expected outputs, and as the source the `optimal` baseline emits.
    - ``gen_inputs(rng)`` deterministically produces one call's positional args from a seeded RNG.
    """

    name: str
    difficulty: Difficulty
    entry_point: str
    prompt: str
    reference: str
    gen_inputs: Callable[[random.Random], tuple]


# --------------------------------------------------------------------------------------------------
# Input generators (deterministic given the RNG) — kept tiny and total.
# --------------------------------------------------------------------------------------------------

def _g_add(rng: random.Random) -> tuple:
    return (rng.randint(-100, 100), rng.randint(-100, 100))


def _g_is_even(rng: random.Random) -> tuple:
    return (rng.randint(-1000, 1000),)


def _rand_word(rng: random.Random, lo: int = 0, hi: int = 12) -> str:
    n = rng.randint(lo, hi)
    return "".join(rng.choice("abcdefghijklmnopqrstuvwxyz") for _ in range(n))


def _g_reverse_string(rng: random.Random) -> tuple:
    return (_rand_word(rng),)


def _g_fib(rng: random.Random) -> tuple:
    return (rng.randint(0, 25),)


def _g_count_vowels(rng: random.Random) -> tuple:
    return (_rand_word(rng, 0, 16),)


def _g_is_palindrome(rng: random.Random) -> tuple:
    # Half the time hand a genuine palindrome, so both branches are exercised.
    base = _rand_word(rng, 1, 6)
    if rng.random() < 0.5:
        return (base + base[::-1],)  # even-length palindrome
    return (_rand_word(rng, 1, 10),)


def _g_is_prime(rng: random.Random) -> tuple:
    return (rng.randint(0, 500),)


def _g_collatz_steps(rng: random.Random) -> tuple:
    return (rng.randint(1, 100),)


def _g_run_length_encode(rng: random.Random) -> tuple:
    # Small alphabet so runs actually occur.
    n = rng.randint(0, 14)
    return ("".join(rng.choice("aabbc") for _ in range(n)),)


# --------------------------------------------------------------------------------------------------
# Reference solutions (the oracle + the `optimal` baseline's emitted source).
# Each defines exactly the task's entry point.
# --------------------------------------------------------------------------------------------------

_REF_ADD = "def add(a, b):\n    return a + b\n"

_REF_IS_EVEN = "def is_even(n):\n    return n % 2 == 0\n"

_REF_REVERSE_STRING = "def reverse_string(s):\n    return s[::-1]\n"

_REF_FIB = (
    "def fib(n):\n"
    "    a, b = 0, 1\n"
    "    for _ in range(n):\n"
    "        a, b = b, a + b\n"
    "    return a\n"
)

_REF_COUNT_VOWELS = (
    "def count_vowels(s):\n"
    "    return sum(1 for c in s if c in 'aeiou')\n"
)

_REF_IS_PALINDROME = "def is_palindrome(s):\n    return s == s[::-1]\n"

_REF_IS_PRIME = (
    "def is_prime(n):\n"
    "    if n < 2:\n"
    "        return False\n"
    "    i = 2\n"
    "    while i * i <= n:\n"
    "        if n % i == 0:\n"
    "            return False\n"
    "        i += 1\n"
    "    return True\n"
)

_REF_COLLATZ = (
    "def collatz_steps(n):\n"
    "    steps = 0\n"
    "    while n != 1:\n"
    "        n = n // 2 if n % 2 == 0 else 3 * n + 1\n"
    "        steps += 1\n"
    "    return steps\n"
)

_REF_RLE = (
    "def run_length_encode(s):\n"
    "    if not s:\n"
    "        return ''\n"
    "    out = []\n"
    "    prev = s[0]\n"
    "    count = 1\n"
    "    for c in s[1:]:\n"
    "        if c == prev:\n"
    "            count += 1\n"
    "        else:\n"
    "            out.append(prev + str(count))\n"
    "            prev = c\n"
    "            count = 1\n"
    "    out.append(prev + str(count))\n"
    "    return ''.join(out)\n"
)


TASK_SUITE: tuple[CodingTask, ...] = (
    # --- easy ---
    CodingTask(
        "add", Difficulty.EASY, "add",
        "Return the sum of two integers a and b.",
        _REF_ADD, _g_add,
    ),
    CodingTask(
        "is_even", Difficulty.EASY, "is_even",
        "Return True if the integer n is even, else False.",
        _REF_IS_EVEN, _g_is_even,
    ),
    CodingTask(
        "reverse_string", Difficulty.EASY, "reverse_string",
        "Return the string s reversed.",
        _REF_REVERSE_STRING, _g_reverse_string,
    ),
    # --- medium ---
    CodingTask(
        "fib", Difficulty.MEDIUM, "fib",
        "Return the nth Fibonacci number (0-indexed: fib(0)=0, fib(1)=1).",
        _REF_FIB, _g_fib,
    ),
    CodingTask(
        "count_vowels", Difficulty.MEDIUM, "count_vowels",
        "Return the number of vowels (aeiou) in the lowercase string s.",
        _REF_COUNT_VOWELS, _g_count_vowels,
    ),
    CodingTask(
        "is_palindrome", Difficulty.MEDIUM, "is_palindrome",
        "Return True if the string s reads the same forwards and backwards.",
        _REF_IS_PALINDROME, _g_is_palindrome,
    ),
    # --- hard ---
    CodingTask(
        "is_prime", Difficulty.HARD, "is_prime",
        "Return True if the integer n is a prime number, else False.",
        _REF_IS_PRIME, _g_is_prime,
    ),
    CodingTask(
        "collatz_steps", Difficulty.HARD, "collatz_steps",
        "Return how many Collatz steps the positive integer n takes to reach 1.",
        _REF_COLLATZ, _g_collatz_steps,
    ),
    CodingTask(
        "run_length_encode", Difficulty.HARD, "run_length_encode",
        "Run-length encode s: 'aaabb' -> 'a3b2'; '' -> ''.",
        _REF_RLE, _g_run_length_encode,
    ),
)
