"""Park-orchestrated HTTP/JSON server for bring-your-own (BYO) agents (decision D-027).

This is the wire realisation of D-015: the **park drives the loop**. The park runs the
negotiation suite in a background thread; whenever the external test agent (side "A") is
on turn, the park publishes a JSON `Observation` and then blocks until the agent posts back
a JSON `Action`. The negotiation itself is still executed by the existing `engine.py` /
`suite.py`, and the result is written by the existing `runlog.py` — nothing about the
match logic or the run-log schema changes. The HTTP layer only *transports* the protocol
objects that `protocol.py` already defines.

Wire protocol (turn-based, request/response, stdlib only — no new dependencies):

  GET  /observation
      -> 200 {"status": "your_turn", "turn": <int>, "observation": {...}}
         when it is the external agent's turn; `observation` is `Observation.to_dict`-style.
      -> 200 {"status": "waiting"}   the park is busy (e.g. the house persona is moving).
      -> 200 {"status": "done", "profile": {...}}   the whole run has finished.

  POST /action      body: an `Action`-shaped JSON object ({"type", "offer", "message"})
      -> 200 {"status": "accepted", "turn": <int>}
      -> 409 {"error": "..."}    if it is not currently the agent's turn.

  GET  /health      -> 200 {"status": "ok", "agent": "<name>"}

A BYO agent is therefore a pure HTTP *client*: poll `/observation`, and whenever it is its
turn, compute and `POST /action`. No inbound server is required on the agent's side, which
keeps the contract universal across agent frameworks.

`Observation` carries only the acting agent's OWN utilities (information asymmetry, D-016),
so serialising it over the wire leaks nothing about the house persona's preferences.
"""

from __future__ import annotations

import json
import queue
import threading
from dataclasses import dataclass
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Optional

from .agents.base import Agent
from .protocol import Action, ActionType, Observation, Offer
from .runlog import write_run
from .scoring import Profile
from .suite import Suite, run_suite

# --- Serialisation helpers (build on the existing protocol.py to_dict/from_dict) ----------


def observation_to_dict(obs: Observation) -> dict:
    """Serialise an Observation for the wire. Mirrors the in-process protocol exactly."""
    return {
        "role": obs.role,
        "my_util": [list(row) for row in obs.my_util],
        "standing_offer": obs.standing_offer.to_dict() if obs.standing_offer else None,
        "my_last_offer": obs.my_last_offer.to_dict() if obs.my_last_offer else None,
        "rounds_left": obs.rounds_left,
        "history": list(obs.history),
    }


def observation_from_dict(d: dict) -> Observation:
    """Rebuild an Observation from its wire form (used by the in-process test client)."""
    return Observation(
        role=d["role"],
        my_util=tuple(tuple(float(x) for x in row) for row in d["my_util"]),
        standing_offer=Offer.from_dict(d["standing_offer"]) if d.get("standing_offer") else None,
        my_last_offer=Offer.from_dict(d["my_last_offer"]) if d.get("my_last_offer") else None,
        rounds_left=int(d["rounds_left"]),
        history=tuple(d.get("history", [])),
    )


def action_from_dict(d: dict) -> Action:
    """Rebuild an Action from its wire form. `Action.to_dict` is the inverse."""
    a_type = ActionType(d["type"])
    offer_d = d.get("offer")
    offer = Offer.from_dict(offer_d) if offer_d else None
    return Action(type=a_type, offer=offer, message=d.get("message", ""))


# --- The bridge agent: lives inside run_suite, blocks on the network ----------------------


@dataclass
class Pending:
    """An observation awaiting the external agent's action, plus per-turn metadata."""

    turn: int
    obs: Observation
    match: Optional[dict]  # {"seed", "total_rounds"} on the first turn of a match, else None


class HttpBridgeAgent(Agent):
    """Side-A agent stub the park runs locally; each `act()` is answered over HTTP.

    The park's negotiation loop calls `act(obs)` synchronously. This implementation hands the
    observation to the HTTP server (via a thread-safe queue) and blocks until the external
    agent has POSTed the corresponding action back. That keeps the engine and scoring
    completely unchanged — from their point of view this is just another `Agent`.
    """

    def __init__(self, name: str = "byo-http") -> None:
        self.name = name
        self._obs_q: "queue.Queue[Pending]" = queue.Queue(maxsize=1)
        self._act_q: "queue.Queue[Action]" = queue.Queue(maxsize=1)
        self._turn = 0
        self._lock = threading.Lock()
        # Per-match reset params, captured from the park's reset() call. The first turn of
        # each match carries these to the client so a seed-dependent BYO agent can re-seed
        # identically to a pure in-process run (determinism parity, D-027). The heuristic
        # stand-in is seed-independent, but a general agent need not be.
        self._pending_match: Optional[dict] = None

    # -- engine-facing side --
    def reset(self, seed: int = 0, total_rounds: int = 8) -> None:
        super().reset(seed=seed, total_rounds=total_rounds)
        # run_suite() calls reset() once per match; tag the next turn as a new match.
        self._pending_match = {"seed": seed, "total_rounds": total_rounds}

    def act(self, obs: Observation) -> Action:
        with self._lock:
            self._turn += 1
            turn = self._turn
            match = self._pending_match
            self._pending_match = None
        self._obs_q.put(Pending(turn=turn, obs=obs, match=match))
        return self._act_q.get()

    # -- server-facing side --
    def take_pending(self) -> "Optional[Pending]":
        """Non-blocking peek+pop of the observation awaiting the external agent, if any."""
        try:
            return self._obs_q.get_nowait()
        except queue.Empty:
            return None

    def submit_action(self, action: Action) -> None:
        self._act_q.put(action)


class _RunState:
    """Shared state between the HTTP handler threads and the park's run thread."""

    def __init__(self, agent: HttpBridgeAgent) -> None:
        self.agent = agent
        self.pending: Optional[Pending] = None
        self.profile: Optional[Profile] = None
        self.records: Optional[list] = None
        self.error: Optional[str] = None
        self.done = threading.Event()
        # Serialises access to `pending` across the threaded HTTP handlers.
        self.lock = threading.Lock()


def _make_handler(state: _RunState):
    class Handler(BaseHTTPRequestHandler):
        # Silence the default request logging so test output stays clean.
        def log_message(self, *_args) -> None:  # noqa: D401
            return

        def _send(self, code: int, payload: dict) -> None:
            body = json.dumps(payload).encode("utf-8")
            self.send_response(code)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self) -> None:  # noqa: N802
            path = self.path.split("?", 1)[0].rstrip("/")
            if path in ("", "/health"):
                self._send(200, {"status": "ok", "agent": state.agent.name})
                return
            if path == "/observation":
                self._handle_observation()
                return
            self._send(404, {"error": f"unknown path {self.path!r}"})

        def do_POST(self) -> None:  # noqa: N802
            path = self.path.split("?", 1)[0].rstrip("/")
            if path == "/action":
                self._handle_action()
                return
            self._send(404, {"error": f"unknown path {self.path!r}"})

        # -- handlers --
        def _handle_observation(self) -> None:
            if state.error is not None:
                self._send(500, {"status": "error", "error": state.error})
                return
            with state.lock:
                # If we are not already holding an observation, try to pick one up.
                if state.pending is None:
                    state.pending = state.agent.take_pending()
                pending = state.pending
            if pending is not None:
                payload = {
                    "status": "your_turn",
                    "turn": pending.turn,
                    "observation": observation_to_dict(pending.obs),
                }
                if pending.match is not None:
                    # First turn of a match: let a seed-dependent client re-seed identically.
                    payload["new_match"] = pending.match
                self._send(200, payload)
                return
            if state.done.is_set():
                from .runlog import _profile_to_dict  # local import; same module family
                prof = _profile_to_dict(state.profile) if state.profile else None
                self._send(200, {"status": "done", "profile": prof})
                return
            self._send(200, {"status": "waiting"})

        def _handle_action(self) -> None:
            length = int(self.headers.get("Content-Length", 0))
            try:
                raw = self.rfile.read(length) if length else b"{}"
                action = action_from_dict(json.loads(raw.decode("utf-8")))
            except (ValueError, KeyError) as exc:
                self._send(400, {"error": f"bad action: {exc}"})
                return
            with state.lock:
                # Maybe one is waiting but /observation was never polled — try once.
                if state.pending is None:
                    state.pending = state.agent.take_pending()
                pending = state.pending
                if pending is None:
                    self._send(409, {"error": "not your turn (no pending observation)"})
                    return
                state.pending = None
            state.agent.submit_action(action)
            self._send(200, {"status": "accepted", "turn": pending.turn})

    return Handler


class ParkServer:
    """Hosts a single negotiation run; side A is answered by the external HTTP agent.

    Usage:
        srv = ParkServer(suite, host="127.0.0.1", port=0, agent_name="byo")
        srv.start()                 # binds, spawns the run thread, returns immediately
        ...  external agent polls /observation and posts /action ...
        profile, records = srv.wait()   # blocks until the run finishes
        srv.stop()
    """

    def __init__(
        self,
        suite: Suite,
        host: str = "127.0.0.1",
        port: int = 0,
        agent_name: str = "byo-http",
        write_log: bool = True,
        log_root: str = "runs",
    ) -> None:
        self.suite = suite
        self.host = host
        self.port = port
        self.agent_name = agent_name
        self.write_log = write_log
        self.log_root = log_root
        self.agent = HttpBridgeAgent(name=agent_name)
        self._state = _RunState(self.agent)
        self._httpd: Optional[ThreadingHTTPServer] = None
        self._serve_thread: Optional[threading.Thread] = None
        self._run_thread: Optional[threading.Thread] = None

    @property
    def address(self) -> tuple[str, int]:
        if self._httpd is None:
            raise RuntimeError("server not started")
        return self._httpd.server_address[0], self._httpd.server_address[1]

    @property
    def base_url(self) -> str:
        host, port = self.address
        return f"http://{host}:{port}"

    def start(self) -> "ParkServer":
        handler = _make_handler(self._state)
        self._httpd = ThreadingHTTPServer((self.host, self.port), handler)
        self.port = self._httpd.server_address[1]
        self._serve_thread = threading.Thread(
            target=self._httpd.serve_forever, name="parkbench-http", daemon=True
        )
        self._serve_thread.start()
        self._run_thread = threading.Thread(
            target=self._run, name="parkbench-run", daemon=True
        )
        self._run_thread.start()
        return self

    def _run(self) -> None:
        try:
            profile, records = run_suite(self.suite, self.agent)
            self._state.profile = profile
            self._state.records = records
            if self.write_log:
                write_run(profile, records, self.suite, out_root=self.log_root)
        except Exception as exc:  # surface to clients via /observation
            self._state.error = repr(exc)
        finally:
            self._state.done.set()

    def wait(self, timeout: Optional[float] = None) -> tuple[Profile, list]:
        self._state.done.wait(timeout=timeout)
        if self._state.error is not None:
            raise RuntimeError(f"park run failed: {self._state.error}")
        assert self._state.profile is not None
        return self._state.profile, self._state.records or []

    def stop(self) -> None:
        if self._httpd is not None:
            self._httpd.shutdown()
            self._httpd.server_close()
            self._httpd = None
