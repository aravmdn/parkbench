"""A reference HTTP client that drives a local commons agent over the park's wire (D-075).

The commons counterpart of `client.py` (negotiation) and `solo_client.py` (the plan wire). It lets
any existing commons agent (e.g. ``parkbench.commons.make_agent("heuristic")``) be served to a
:class:`~parkbench.commons_server.CommonsParkServer` as if it were an external bring-your-own agent,
using only `urllib` from the stdlib. It is the canonical example of how a third party connects to the
commons ride: poll ``/observation``, and whenever a round is waiting, choose a contribution locally
and ``POST /contribution``.

Because the park drives the loop (D-015), this client has no game logic of its own — every decision
belongs to the wrapped agent. That is the property that makes it a *reference* client rather than a
second implementation of the ride: swap the agent and the transport is unchanged; swap the transport
and the score must not move.
"""

from __future__ import annotations

import json
import time
import urllib.error
import urllib.request

from .commons_protocol import history_from_list, scenario_from_dict


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


def drive_commons_agent(
    base_url: str,
    agent,
    poll_interval: float = 0.0,
    timeout: float = 30.0,
    max_steps: int = 100_000,
) -> dict:
    """Run ``agent`` against a `CommonsParkServer` at ``base_url`` until the run reports "done".

    Returns the server's final ``{"status": "done", "result": {...}}`` payload.

    ``agent`` is any object with the commons agent shape — ``reset(seed=...)`` and
    ``contribute(round_idx, history, scenario)`` returning an int.

    The park re-seeds the agent once per game (see :func:`parkbench.commons.suite.run_suite`) and
    forwards that seed in ``new_game`` on round 0 **only**; this client re-seeds the wrapped agent
    exactly when it is told to, so a seed-dependent BYO agent (the `random` baseline, say) reproduces
    the pure in-process run exactly. Re-seeding on every round would restart the RNG mid-game and
    quietly produce a different — but still plausible-looking — score.
    """
    base = base_url.rstrip("/")
    for _ in range(max_steps):
        try:
            state = _get_json(f"{base}/observation", timeout=timeout)
        except urllib.error.HTTPError as exc:
            # A 500 carries the park's own error text — surface it rather than a bare status code.
            raise RuntimeError(f"park reported an error: {exc.read().decode('utf-8')}") from None
        except urllib.error.URLError:
            # Server not up yet (or momentarily closed) — back off briefly and retry.
            time.sleep(0.01)
            continue
        status = state.get("status")
        if status == "done":
            return state
        if status == "your_turn":
            new_game = state.get("new_game")
            if new_game is not None:
                agent.reset(seed=int(new_game["seed"]))
            scenario = scenario_from_dict(state["scenario"])
            history = history_from_list(state["history"])
            contribution = int(agent.contribute(int(state["round_idx"]), history, scenario))
            _post_json(f"{base}/contribution", {"contribution": contribution}, timeout=timeout)
            continue
        if status == "error":
            raise RuntimeError(f"park reported an error: {state.get('error')}")
        # "waiting" — the park is between games; poll again.
        if poll_interval:
            time.sleep(poll_interval)
    raise RuntimeError("drive_commons_agent exceeded max_steps without the run finishing")
