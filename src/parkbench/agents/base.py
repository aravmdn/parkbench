"""The agent interface every participant implements (house or bring-your-own)."""

from __future__ import annotations

import abc
import hashlib
import json
import random
from dataclasses import dataclass

from .. import __version__ as _PACKAGE_VERSION
from ..protocol import Action, Observation


@dataclass(frozen=True)
class AgentIdentity:
    """A stable, attributable identity for an agent (decision D-038).

    Stamped into every run log so results stay attributable and reproducible over time:

      - ``name``        — the agent's name (its ``Agent.name``).
      - ``version``     — the agent's version (defaults to the package version, else "0").
      - ``config_hash`` — a short, deterministic hash of the agent's defining config/params,
                          so two agents with different settings get distinct identities while
                          the *same* agent + the *same* code always hashes identically.
    """

    name: str
    version: str
    config_hash: str

    def to_dict(self) -> dict:
        return {"name": self.name, "version": self.version, "config_hash": self.config_hash}


def config_hash(config: dict | None) -> str:
    """A short, stable hash of an agent's defining config.

    Deterministic across processes and instances: same code + same config => same hash
    (it hashes a canonical JSON encoding, never memory addresses). An empty/None config
    hashes to a fixed sentinel so configless agents still get a stable identity.
    """
    payload = json.dumps(config or {}, sort_keys=True, default=str, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:12]


class Agent(abc.ABC):
    name: str = "agent"
    version: str = _PACKAGE_VERSION

    def reset(self, seed: int = 0, total_rounds: int = 8) -> None:
        """Called once before each match: re-seed the RNG and clear per-match state.

        Re-seeding here is what makes whole suites reproducible (the v1 claim).
        """
        self.rng = random.Random(seed)
        self.total_rounds = total_rounds

    @abc.abstractmethod
    def act(self, obs: Observation) -> Action:
        """Return this agent's move for the given observation."""

    # -- identity & versioning (decision D-038) ------------------------------

    def config(self) -> dict:
        """The agent's *defining* configuration, used to compute ``config_hash``.

        Override to declare the parameters that distinguish this agent's behaviour
        (e.g. concession schedule, model id). Two agents that behave identically should
        return equal configs; agents that differ should differ here. The default is an
        empty config, which is correct for parameterless agents.
        """
        return {}

    def identity(self) -> AgentIdentity:
        """A stable, attributable identity for this agent (decision D-038).

        Deterministic: the same agent class + same config + same code always yields the
        same identity, independent of instance or process. Backward compatible — every
        existing agent gets a sensible identity with no changes.
        """
        return AgentIdentity(
            name=self.name,
            version=getattr(self, "version", None) or _PACKAGE_VERSION or "0",
            config_hash=config_hash(self.config()),
        )
