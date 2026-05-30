"""A reference HTTP client that drives a local `Agent` over the park's wire protocol.

This is the small in-process adapter the task calls for: it lets any existing `Agent`
(e.g. `HeuristicNegotiator`) be served to a `ParkServer` as if it were an external
bring-your-own agent, using only `urllib` from the stdlib (no new dependencies). It is the
canonical example of how a third party would connect: poll `/observation`, and whenever it
is its turn, compute an `Action` locally and `POST /action`.

Because the park drives the loop (D-015), this client is a thin poll loop with no game
logic of its own — all the negotiation behaviour lives in the wrapped `Agent`.
"""

from __future__ import annotations

import json
import time
import urllib.error
import urllib.request

from .agents.base import Agent
from .server import observation_from_dict


def _get_json(url: str, timeout: float) -> dict:
    req = urllib.request.Request(url, method="GET")
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _post_json(url: str, payload: dict, timeout: float) -> dict:
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url, data=data, method="POST", headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def drive_agent(
    base_url: str,
    agent: Agent,
    poll_interval: float = 0.0,
    timeout: float = 30.0,
    max_steps: int = 100_000,
) -> dict:
    """Run `agent` against a `ParkServer` at `base_url` until the run reports "done".

    Returns the server's final `{"status": "done", "profile": {...}}` payload.

    The park re-seeds its *own* side-A bridge per match for determinism (see
    `suite.run_suite`) and forwards the match's `seed`/`total_rounds` to this client on the
    first turn of each match (the `new_match` field). The client re-seeds the wrapped agent
    with the same values, so a seed-dependent BYO agent reproduces the pure in-process run
    exactly. (The heuristic stand-in is seed-independent, so parity holds regardless.)
    """
    agent.reset(seed=0, total_rounds=8)
    base = base_url.rstrip("/")
    for _ in range(max_steps):
        try:
            state = _get_json(f"{base}/observation", timeout=timeout)
        except urllib.error.URLError:
            # Server not up yet (or momentarily closed) — back off briefly and retry.
            time.sleep(0.01)
            continue
        status = state.get("status")
        if status == "done":
            return state
        if status == "your_turn":
            new_match = state.get("new_match")
            if new_match is not None:
                agent.reset(
                    seed=int(new_match["seed"]),
                    total_rounds=int(new_match["total_rounds"]),
                )
            obs = observation_from_dict(state["observation"])
            action = agent.act(obs)
            _post_json(f"{base}/action", action.to_dict(), timeout=timeout)
            continue
        if status == "error":
            raise RuntimeError(f"park reported an error: {state.get('error')}")
        # "waiting" — the park is processing the house side; poll again.
        if poll_interval:
            time.sleep(poll_interval)
    raise RuntimeError("drive_agent exceeded max_steps without the run finishing")
