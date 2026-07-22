"""The read-only profiles HTTP endpoint (chunk-4 ``serve-profiles-endpoint``).

The central claim: ``GET /radar`` / ``/career`` / ``/leaderboard`` return the **exact** JSON the CLI
already emits for ``radar`` / ``career`` / ``leaderboard --json`` — same producers, same
``benchmark_version`` stamp (D-061). That parity is what lets the ``web/`` app (and the ``viewer/``
pages) ``fetch`` a live profile instead of importing a build-time fixture, with zero new scoring code
(presentation-only, D-012).

Everything runs in-process on an ephemeral port (``port=0``); no external network.
"""

from __future__ import annotations

import json
import urllib.error
import urllib.request

from parkbench import BENCHMARK_VERSION, cli
from parkbench.profiles_server import ProfilesServer


def _get(base_url: str, path: str) -> tuple[int, dict]:
    """GET ``base_url + path``; return ``(status_code, parsed_json_body)`` (handles error codes)."""
    try:
        with urllib.request.urlopen(base_url + path, timeout=10) as resp:
            return resp.status, json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        return exc.code, json.loads(exc.read().decode("utf-8"))


def _cli_json(argv: list[str], capsys) -> dict:
    """Run the real CLI with ``argv`` and return its parsed ``--json`` stdout (the source of truth)."""
    assert cli.main(argv) == 0
    return json.loads(capsys.readouterr().out)


# --- served JSON is byte-parity with the CLI producers ------------------------------------


def test_radar_endpoint_matches_cli_json(capsys):
    ref = _cli_json(["radar", "--agent", "heuristic", "--seed", "1", "--json"], capsys)
    srv = ProfilesServer(host="127.0.0.1", port=0).start()
    try:
        status, body = _get(srv.base_url, "/radar?agent=heuristic&seed=1")
    finally:
        srv.stop()
    assert status == 200
    assert body == ref
    assert body["benchmark_version"] == BENCHMARK_VERSION


def test_career_endpoint_matches_cli_json_for_reward_hacker(capsys):
    # greedy is the reward-hacker whose reputation collapses — a good contrasting case.
    ref = _cli_json(["career", "--agent", "greedy", "--seed", "1", "--json"], capsys)
    srv = ProfilesServer(host="127.0.0.1", port=0).start()
    try:
        status, body = _get(srv.base_url, "/career?agent=greedy&seed=1")
    finally:
        srv.stop()
    assert status == 200
    assert body == ref


def test_leaderboard_endpoint_matches_cli_json(capsys):
    ref = _cli_json(["leaderboard", "--seed", "1", "--json"], capsys)
    srv = ProfilesServer(host="127.0.0.1", port=0).start()
    try:
        status, body = _get(srv.base_url, "/leaderboard?seed=1")
    finally:
        srv.stop()
    assert status == 200
    assert body == ref
    # The default roster ranking is present and version-stamped.
    assert [r["agent"] for r in body["ranking"]]
    assert body["benchmark_version"] == BENCHMARK_VERSION


def test_default_agent_and_seed_match_cli_defaults(capsys):
    """Bare /radar (no query) must equal `radar --json` with the CLI's default agent+seed."""
    ref = _cli_json(["radar", "--json"], capsys)  # CLI defaults: agent=heuristic, seed=1
    srv = ProfilesServer(host="127.0.0.1", port=0, default_seed=1).start()
    try:
        status, body = _get(srv.base_url, "/radar")
    finally:
        srv.stop()
    assert status == 200
    assert body == ref


# --- routing / error handling -------------------------------------------------------------


def test_unknown_route_404s():
    srv = ProfilesServer(host="127.0.0.1", port=0).start()
    try:
        status, body = _get(srv.base_url, "/nope")
    finally:
        srv.stop()
    assert status == 404
    assert "unknown path" in body["error"]


def test_unknown_agent_400s():
    srv = ProfilesServer(host="127.0.0.1", port=0).start()
    try:
        status, body = _get(srv.base_url, "/radar?agent=not-a-real-agent")
    finally:
        srv.stop()
    assert status == 400
    assert "unknown agent" in body["error"]


def test_bad_seed_400s():
    srv = ProfilesServer(host="127.0.0.1", port=0).start()
    try:
        status, body = _get(srv.base_url, "/leaderboard?seed=notanumber")
    finally:
        srv.stop()
    assert status == 400
    assert "bad seed" in body["error"]


def test_health_endpoint():
    srv = ProfilesServer(host="127.0.0.1", port=0).start()
    try:
        status, body = _get(srv.base_url, "/health")
    finally:
        srv.stop()
    assert status == 200
    assert body["status"] == "ok"
    assert body["service"] == "parkbench-profiles"
    assert body["benchmark_version"] == BENCHMARK_VERSION


def test_post_is_rejected_read_only():
    srv = ProfilesServer(host="127.0.0.1", port=0).start()
    try:
        req = urllib.request.Request(srv.base_url + "/radar", data=b"{}", method="POST")
        try:
            urllib.request.urlopen(req, timeout=10)
            status = 200
        except urllib.error.HTTPError as exc:
            status = exc.code
    finally:
        srv.stop()
    assert status == 405


def test_response_carries_cors_header():
    """web/ (served from Vite on another port) must be able to fetch cross-origin."""
    srv = ProfilesServer(host="127.0.0.1", port=0).start()
    try:
        with urllib.request.urlopen(srv.base_url + "/leaderboard", timeout=10) as resp:
            assert resp.headers.get("Access-Control-Allow-Origin") == "*"
            assert resp.headers.get("Content-Type") == "application/json"
    finally:
        srv.stop()
