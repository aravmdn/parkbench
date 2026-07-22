"""Read-only HTTP endpoint that serves the diagnostic-profile JSON (chunk-4 ``serve-profiles-endpoint``).

``parkbench serve --profiles`` starts a tiny **stdlib** ``http.server`` (no new dependencies, upholds
D-023) that answers GET requests with the *verbatim* ``--json`` output the CLI already emits for
``radar`` / ``career`` / ``leaderboard``. It reuses the exact same producers
(:func:`parkbench.radar.build_radar`, :func:`parkbench.career.build_career`,
:func:`parkbench.career.build_leaderboard`) and the same ``benchmark_version`` stamp (D-061) — it
computes **nothing**. It is the **live-data** counterpart to the static ``export-profiles`` fixture
flow (D-062): where the exporter writes fixtures to disk, this serves them fresh on demand, so the
``web/`` app (and the static ``viewer/`` pages) can ``fetch`` a profile instead of importing a
build-time fixture.

> **Presentation-only (D-012):** this only *serves existing producers' JSON* — no scoring logic, no
> ride/scoring code path lives here. It resolves the "live read-only profiles endpoint" open question
> in ``docs/04-open-questions.md`` (the other half of the ``live-profiles`` task, D-062).

Routes (GET only; the whole surface is read-only):

  GET /radar?agent=<name>&seed=<int>     -> radar --json for that agent
  GET /career?agent=<name>&seed=<int>    -> career --json for that agent
  GET /leaderboard?seed=<int>            -> leaderboard --json (default roster)
  GET /health                            -> {"status": "ok", "service": "parkbench-profiles", ...}

``agent`` defaults to ``heuristic`` and ``seed`` to the server's default (1) — matching the CLI
defaults — so the bare ``/radar`` and ``/career`` paths work. An unknown ``agent`` or a bad ``seed``
is a ``400``; any other path is a ``404``; any non-GET method is a ``405``. Every JSON body is stamped
exactly as the CLI's ``_emit_json`` prints it (``benchmark_version`` first), so a byte-parity test can
pin the served payloads to the CLI forever (see ``tests/test_serve_profiles.py``). Responses carry a
permissive ``Access-Control-Allow-Origin: *`` header so the Vite-served ``web/`` app can ``fetch``
cross-origin — safe because the surface is read-only and exposes only public benchmark scores.
"""

from __future__ import annotations

import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Optional
from urllib.parse import parse_qs, urlparse

from . import BENCHMARK_VERSION

DEFAULT_SEED = 1
DEFAULT_AGENT = "heuristic"  # matches the CLI's radar/career --agent default


def known_agents() -> set[str]:
    """The union roster the CLI's ``radar``/``career`` accept — used to reject unknown agents.

    Identical to ``cli.build_parser``'s ``radar_agents`` union (each ride owns its own roster, D-035);
    computed lazily so importing this module never forces the whole ride graph to load.
    """
    from .agents import AGENT_REGISTRY
    from .coding import AGENT_REGISTRY as CODE_AGENTS
    from .commons import AGENT_REGISTRY as COMMONS_AGENTS
    from .economic import AGENT_REGISTRY as ECON_AGENTS
    from .safety import AGENT_REGISTRY as SAFE_AGENTS

    return (
        set(AGENT_REGISTRY)
        | set(COMMONS_AGENTS)
        | set(ECON_AGENTS)
        | set(CODE_AGENTS)
        | set(SAFE_AGENTS)
    )


def build_profile_payload(kind: str, agent: Optional[str] = None, seed: int = DEFAULT_SEED) -> dict:
    """Return the stamped ``--json`` payload for ``kind`` — identical to what the CLI emits.

    ``kind`` is ``"radar"``, ``"career"`` or ``"leaderboard"``. The ``benchmark_version`` stamp is
    prepended exactly as ``parkbench.cli._emit_json`` does (D-061), so the served body is byte-for-byte
    the CLI's output. Producers are imported lazily (mirrors the CLI's lazy-import style).
    """
    from .career import build_career, build_leaderboard
    from .radar import build_radar

    if kind == "radar":
        payload = build_radar(agent, seed=seed).to_dict()
    elif kind == "career":
        payload = build_career(agent, seed=seed).to_dict()
    elif kind == "leaderboard":
        payload = {"seed": seed, "ranking": [p.to_dict() for p in build_leaderboard(seed=seed)]}
    else:
        raise ValueError(f"unknown profile kind: {kind!r}")
    # Stamp first, exactly like cli._emit_json — a stored/served score is never version-ambiguous.
    return {"benchmark_version": BENCHMARK_VERSION, **payload}


def _make_handler(default_seed: int):
    class ProfilesHandler(BaseHTTPRequestHandler):
        # Silence the default per-request logging so test output stays clean (mirrors server.py).
        def log_message(self, *_args) -> None:  # noqa: D401
            return

        def _send(self, code: int, payload: dict) -> None:
            body = json.dumps(payload).encode("utf-8")
            self.send_response(code)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            # Read-only + public scores => safe to allow any origin so web/ can fetch cross-origin.
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(body)

        def _seed_from(self, query: dict) -> int:
            raw = query.get("seed", [str(default_seed)])[0]
            return int(raw)  # ValueError bubbles up to the do_GET handler -> 400

        def _agent_from(self, query: dict) -> str:
            agent = query.get("agent", [DEFAULT_AGENT])[0] or DEFAULT_AGENT
            if agent not in known_agents():
                raise LookupError(agent)
            return agent

        def do_GET(self) -> None:  # noqa: N802
            parsed = urlparse(self.path)
            path = parsed.path.rstrip("/")
            query = parse_qs(parsed.query)
            if path in ("", "/health"):
                self._send(
                    200,
                    {
                        "status": "ok",
                        "service": "parkbench-profiles",
                        "benchmark_version": BENCHMARK_VERSION,
                        "routes": ["/radar", "/career", "/leaderboard", "/health"],
                    },
                )
                return
            try:
                if path == "/leaderboard":
                    self._send(200, build_profile_payload("leaderboard", seed=self._seed_from(query)))
                    return
                if path in ("/radar", "/career"):
                    kind = path.lstrip("/")
                    agent = self._agent_from(query)
                    seed = self._seed_from(query)
                    self._send(200, build_profile_payload(kind, agent=agent, seed=seed))
                    return
            except ValueError:  # bad ?seed=
                self._send(400, {"error": f"bad seed in {self.path!r}"})
                return
            except LookupError as exc:  # unknown ?agent=
                self._send(400, {"error": f"unknown agent {str(exc)!r}"})
                return
            self._send(404, {"error": f"unknown path {self.path!r}"})

        def _reject_write(self) -> None:
            self._send(405, {"error": "read-only endpoint (GET only)"})

        # The endpoint is strictly read-only; anything that could mutate is refused explicitly.
        do_POST = _reject_write  # noqa: N815
        do_PUT = _reject_write  # noqa: N815
        do_DELETE = _reject_write  # noqa: N815

    return ProfilesHandler


class ProfilesServer:
    """A tiny read-only HTTP host for the ``radar``/``career``/``leaderboard`` JSON.

    Usage (also how the tests drive it, on an ephemeral ``port=0``)::

        srv = ProfilesServer(host="127.0.0.1", port=0).start()
        ... GET srv.base_url + "/radar?agent=heuristic" ...
        srv.stop()
    """

    def __init__(
        self, host: str = "127.0.0.1", port: int = 8080, default_seed: int = DEFAULT_SEED
    ) -> None:
        self.host = host
        self.port = port
        self.default_seed = default_seed
        self._httpd: Optional[ThreadingHTTPServer] = None
        self._thread: Optional[threading.Thread] = None

    @property
    def address(self) -> tuple[str, int]:
        if self._httpd is None:
            raise RuntimeError("server not started")
        return self._httpd.server_address[0], self._httpd.server_address[1]

    @property
    def base_url(self) -> str:
        host, port = self.address
        return f"http://{host}:{port}"

    def start(self) -> "ProfilesServer":
        handler = _make_handler(self.default_seed)
        self._httpd = ThreadingHTTPServer((self.host, self.port), handler)
        self.port = self._httpd.server_address[1]
        self._thread = threading.Thread(
            target=self._httpd.serve_forever, name="parkbench-profiles-http", daemon=True
        )
        self._thread.start()
        return self

    def serve_forever(self) -> None:
        """Block the calling thread until :meth:`stop` (used by the CLI ``serve --profiles``)."""
        if self._httpd is None:
            self.start()
        assert self._thread is not None
        self._thread.join()

    def stop(self) -> None:
        if self._httpd is not None:
            self._httpd.shutdown()
            self._httpd.server_close()
            self._httpd = None
