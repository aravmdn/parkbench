"""Parkbench — a modular benchmark arena for AI agents, themed as a theme park.

v1 ships one ride: a multi-issue integrative negotiation, scored by objective payoff
vs. baselines. See docs/00-vision.md and docs/01-v1-scope.md.
"""

__version__ = "0.0.1"

# The benchmark/generator version (D-061), stamped into every JSON result the CLI emits
# (`radar/career/leaderboard/validity --json`) so a stored score is never ambiguous about which
# benchmark produced it. Deliberately distinct from the package `__version__` (code can change
# without the *measurement* changing). Bumping convention (documented in docs/02-decisions.md,
# D-061): bump when scenario generators, scoring formulas, or default suites/rosters change in a
# way that ALTERS SCORES — major for breaks in comparability, minor for score-altering re-tunes,
# patch for score-neutral generator fixes worth marking. Purely additive reporting (new JSON keys,
# new commands, new measurement harnesses) does NOT bump: scores stay comparable.
BENCHMARK_VERSION = "1.0.0"
