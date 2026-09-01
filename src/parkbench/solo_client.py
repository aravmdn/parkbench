"""A reference HTTP client that drives a local solo-ride agent over the park's wire (D-074).

The solo counterpart of `client.py`. It lets any existing ride agent (e.g.
``parkbench.economic.make_agent("heuristic")``) be served to a :class:`~parkbench.solo_server.
SoloParkServer` as if it were an external bring-your-own agent, using only `urllib` from the stdlib.
It is the canonical example of how a third party connects to a solo ride: poll ``/scenario``, and
whenever a scenario is waiting, compute a plan locally and ``POST /plan``.

Because the park drives the loop (D-015), this client has no game logic of its own — every decision
belongs to the wrapped agent. That is the property that makes it a *reference* client rather than a
second implementation of the rides: swap the agent and the transport is unchanged; swap the transport
and the score must not move.
"""

from __future__ import annotations

import json
import time
import urllib.error
import urllib.request

from .solo_protocol import scenario_from_dict


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


def drive_solo_agent(
    base_url: str,
    agent,
    poll_interval: float = 0.0,
    timeout: float = 30.0,
    max_steps: int = 100_000,
) -> dict:
    """Run ``agent`` against a `SoloParkServer` at ``base_url`` until the run reports "done".

    Returns the server's final ``{"status": "done", "result": {...}}`` payload.

    ``agent`` is any object with the solo-ride agent shape — ``reset(seed=...)`` and
    ``choose(scenario)`` returning a sequence of ints. The ride each scenario belongs to is read off
    the wire (the ``ride`` field), so one client drives all four carried rides without being told
    which it is playing.

    The park re-seeds the agent before every scenario (see
    :func:`parkbench.economic.suite.run_suite` and its siblings) and forwards that seed in
    ``new_scenario``; this client re-seeds the wrapped agent with the same value, so a seed-dependent
    BYO agent (the `random` baseline, say) reproduces the pure in-process run exactly.
    """
    base = base_url.rstrip("/")
    for _ in range(max_steps):
        try:
            state = _get_json(f"{base}/scenario", timeout=timeout)
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
            new_scenario = state.get("new_scenario")
            if new_scenario is not None:
                agent.reset(seed=int(new_scenario["seed"]))
            scenario = scenario_from_dict(state["ride"], state["scenario"])
            plan = [int(x) for x in agent.choose(scenario)]
            _post_json(f"{base}/plan", {"plan": plan}, timeout=timeout)
            continue
        if status == "error":
            raise RuntimeError(f"park reported an error: {state.get('error')}")
        # "waiting" — the park is between scenarios; poll again.
        if poll_interval:
            time.sleep(poll_interval)
    raise RuntimeError("drive_solo_agent exceeded max_steps without the run finishing")
