"""Provider-agnostic LLM reference agent (decision D-030, refines/closes D-025).

This wires a real LLM negotiator against OpenRouter's OpenAI-compatible chat API,
using ONLY the Python standard library (``urllib.request`` + ``json``) so the core
keeps its zero-runtime-dependency promise (decision D-023): no third-party SDK.

Design points:

  - ``Provider`` is the adapter seam (the D-025 interface, now with a concrete
    ``OpenRouterProvider``). Implement ``complete`` to plug in any chat LLM.
  - ``LLMAgent.act`` builds a compact prompt from the Observation — using only the
    acting agent's OWN utilities (preferences are private, decision D-016) — and asks
    the model to reply with a single strict JSON action.
  - It MUST degrade gracefully. On any missing key / network / parse / validation
    failure it silently falls back to the deterministic heuristic move (it reuses
    ``HeuristicNegotiator``'s logic) so a run never crashes or hangs, and it never
    prints to stdout.

Environment variables:
  - ``OPENROUTER_API_KEY``   (required for live calls; absent ⇒ heuristic fallback)
  - ``OPENROUTER_MODEL``     (optional; defaults to ``DEFAULT_MODEL`` below)
"""

from __future__ import annotations

import abc
import json
import os
import urllib.error
import urllib.request
from typing import Optional

from ..protocol import Action, Observation, Offer
from .base import Agent
from .heuristic import HeuristicNegotiator

# A free OpenRouter model id (ends in ":free"). Easily changed here or via the
# OPENROUTER_MODEL env var. Verified available + JSON-capable on 2026-05-30.
DEFAULT_MODEL = "openai/gpt-oss-120b:free"

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
DEFAULT_TIMEOUT = 20.0  # seconds; a run must never hang on the network


class Provider(abc.ABC):
    """Adapter to a chat LLM. Implement this to plug in any provider."""

    @abc.abstractmethod
    def complete(self, messages: list[dict], **opts) -> str:
        """Return the assistant's text reply for a list of chat messages.

        ``messages`` is a list of ``{"role": ..., "content": ...}`` dicts. May raise
        on any transport/decoding error — ``LLMAgent`` catches and falls back.
        """


class OpenRouterProvider(Provider):
    """Calls OpenRouter's OpenAI-compatible chat-completions endpoint via stdlib only.

    No third-party SDK and no new runtime dependency (decisions D-023, D-030).
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        timeout: float = DEFAULT_TIMEOUT,
        url: str = OPENROUTER_URL,
    ) -> None:
        self.api_key = api_key if api_key is not None else os.environ.get("OPENROUTER_API_KEY", "")
        self.model = model or os.environ.get("OPENROUTER_MODEL") or DEFAULT_MODEL
        self.timeout = timeout
        self.url = url

    def complete(self, messages: list[dict], **opts) -> str:
        if not self.api_key:
            raise RuntimeError("OPENROUTER_API_KEY is not set")
        body = {
            "model": self.model,
            "messages": messages,
            "temperature": opts.get("temperature", 0.0),
        }
        if "max_tokens" in opts:
            body["max_tokens"] = opts["max_tokens"]
        data = json.dumps(body).encode("utf-8")
        req = urllib.request.Request(
            self.url,
            data=data,
            method="POST",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                # OpenRouter attribution headers (optional but recommended).
                "HTTP-Referer": "https://github.com/aravmdn/parkbench",
                "X-Title": "Parkbench",
            },
        )
        with urllib.request.urlopen(req, timeout=self.timeout) as resp:  # noqa: S310 (https only)
            payload = json.loads(resp.read().decode("utf-8"))
        return payload["choices"][0]["message"]["content"]


class LLMAgent(Agent):
    """A negotiator driven by an LLM via a ``Provider``, with a heuristic fallback.

    With no provider (or no API key, or any failure) it behaves exactly like the
    deterministic ``HeuristicNegotiator`` so the agent is always runnable.
    """

    name = "llm"

    def __init__(self, provider: Optional[Provider] = None) -> None:
        # If no provider is injected, construct an OpenRouter one from the environment.
        # That provider raises (and we fall back) when no key is configured, so the
        # 'llm' agent is always runnable even without credentials.
        self.provider = provider if provider is not None else OpenRouterProvider()
        self._fallback = HeuristicNegotiator()

    def reset(self, seed: int = 0, total_rounds: int = 8) -> None:
        super().reset(seed, total_rounds)
        self._fallback.reset(seed, total_rounds)

    def config(self) -> dict:
        """The model id defines this agent's behaviour (decision D-038).

        Different models => different identities. The API key is a secret and is never
        part of the identity. ``getattr`` guards providers without a ``model`` attribute.
        """
        return {"model": getattr(self.provider, "model", None)}

    # -- prompt construction -------------------------------------------------

    def build_messages(self, obs: Observation) -> list[dict]:
        """Build the chat messages for one turn.

        Only the acting agent's OWN information is included (private preferences,
        decision D-016): its own per-issue/level payoff table, the standing offer,
        how many rounds remain, and a compact recent history.
        """
        n = obs.n_issues
        n_levels = len(obs.my_util[0]) if n else 0
        # Own payoff table, rounded for a compact prompt.
        my_util = [[round(v, 2) for v in row] for row in obs.my_util]
        standing = list(obs.standing_offer.levels) if obs.standing_offer else None
        standing_value = round(obs.my_value(obs.standing_offer), 2) if obs.standing_offer else None
        recent = [
            {k: ev[k] for k in ("party", "type", "offer", "message") if k in ev}
            for ev in obs.history[-6:]
        ]

        system = (
            "You are an expert multi-issue negotiator playing one side of a bilateral "
            "negotiation. There are several issues; each issue is set to a discrete level "
            "index. Your payoff is the sum of your own per-issue/level values for the agreed "
            "levels; your maximum possible payoff is the sum of each issue's best level for "
            "you. You only know your OWN values, never the counterpart's. Seek value-creating "
            "trades: concede the issues you value least to gain on the issues you value most. "
            "Reply with ONLY a single JSON object and nothing else, no prose, no code fences. "
            'The JSON must be one of:\n'
            '  {"type":"offer","levels":[<one integer level per issue>],"message":"<short text>"}\n'
            '  {"type":"accept","message":"<short text>"}\n'
            '  {"type":"message","message":"<short text>"}\n'
            f"Each level must be an integer in 0..{max(0, n_levels - 1)}; provide exactly "
            f"{n} levels for an offer. Accept only when the standing offer is good for you."
        )
        user = json.dumps(
            {
                "role": obs.role,
                "n_issues": n,
                "n_levels": n_levels,
                "my_value_per_issue_level": my_util,
                "my_max_payoff": round(obs.my_max, 2),
                "standing_offer_from_counterpart": standing,
                "standing_offer_value_to_me": standing_value,
                "my_last_offer": list(obs.my_last_offer.levels) if obs.my_last_offer else None,
                "rounds_left": obs.rounds_left,
                "recent_history": recent,
            },
            separators=(",", ":"),
        )
        return [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ]

    # -- response parsing ----------------------------------------------------

    def parse_action(self, text: str, obs: Observation) -> Action:
        """Parse the model's reply into a validated Action.

        Raises ``ValueError`` on anything malformed or out-of-range so ``act`` can
        fall back. Tolerates code fences and surrounding prose by extracting the
        outermost JSON object.
        """
        obj = _extract_json_object(text)
        atype = obj.get("type")
        message = obj.get("message", "")
        if not isinstance(message, str):
            message = str(message)

        if atype == "accept":
            return Action.accept(message)
        if atype == "message":
            return Action.say(message)
        if atype == "offer":
            levels = obj.get("levels")
            if not isinstance(levels, (list, tuple)):
                raise ValueError("offer is missing a 'levels' list")
            if len(levels) != obs.n_issues:
                raise ValueError(
                    f"offer has {len(levels)} levels, expected {obs.n_issues}"
                )
            parsed: list[int] = []
            for i, lv in enumerate(levels):
                if isinstance(lv, bool) or not isinstance(lv, int):
                    raise ValueError(f"level {i} is not an integer: {lv!r}")
                if not (0 <= lv < len(obs.my_util[i])):
                    raise ValueError(f"level {i}={lv} out of range")
                parsed.append(lv)
            return Action.make_offer(Offer(tuple(parsed)), message)

        raise ValueError(f"unknown action type: {atype!r}")

    # -- the agent move ------------------------------------------------------

    def act(self, obs: Observation) -> Action:
        try:
            text = self.provider.complete(self.build_messages(obs), max_tokens=256)
            return self.parse_action(text, obs)
        except Exception:
            # Any failure (no key, network, timeout, bad/parse, validation) -> a safe,
            # deterministic move. Never print, never raise: a run must not crash/hang.
            return self._fallback.act(obs)


def _extract_json_object(text: str) -> dict:
    """Return the first balanced ``{...}`` JSON object found in ``text``.

    Handles bare JSON, code-fenced JSON, and JSON embedded in prose. Raises
    ``ValueError`` if no valid object is present.
    """
    if not isinstance(text, str):
        raise ValueError("provider returned non-text")
    s = text.strip()
    # Fast path: the whole thing is a JSON object.
    try:
        obj = json.loads(s)
        if isinstance(obj, dict):
            return obj
    except (ValueError, TypeError):
        pass
    # Scan for the first balanced top-level object (string-aware).
    start = s.find("{")
    while start != -1:
        depth = 0
        in_str = False
        escape = False
        for i in range(start, len(s)):
            ch = s[i]
            if in_str:
                if escape:
                    escape = False
                elif ch == "\\":
                    escape = True
                elif ch == '"':
                    in_str = False
                continue
            if ch == '"':
                in_str = True
            elif ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    candidate = s[start : i + 1]
                    try:
                        obj = json.loads(candidate)
                    except ValueError:
                        break  # malformed; try the next '{'
                    if isinstance(obj, dict):
                        return obj
                    break
        start = s.find("{", start + 1)
    raise ValueError("no JSON object found in provider response")
