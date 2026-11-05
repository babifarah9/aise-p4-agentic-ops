"""The policy engine: what the agent may do on its own, with approval, or never.

Decisions depend only on the tool's declaration, the target environment, the
agent's granted scopes and its autonomy level: never on text in the ticket.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .tools import Tool

ALLOW, APPROVE, DENY = "allow", "needs_approval", "deny"


@dataclass(frozen=True)
class Grant:
    env: str
    scopes: frozenset[str]


@dataclass
class Policy:
    """Autonomy levels (Chapter 14):

    0 suggest only: every non-read action needs approval;
    1 act on low-risk, reversible actions; everything else needs approval;
    2 also act on low-risk irreversible actions (e.g. clearing temp files);
    high-risk actions always need approval at every level.
    """

    autonomy: int = 2
    grants: list[Grant] = field(default_factory=lambda: [
        Grant("prod", frozenset({"read", "operate", "deploy", "notify"})),
        Grant("staging", frozenset({"read", "operate", "deploy", "data", "notify"})),
    ])
    max_actions_per_ticket: int = 6
    never: frozenset[str] = frozenset({"delete_volume"})  # not even with approval, in prod

    def decide(self, tool: Tool, env: str) -> tuple[str, str]:
        if tool.name in self.never and env == "prod":
            return DENY, f"{tool.name} is never run by the agent in prod"
        grant = next((g for g in self.grants if g.env == env), None)
        if grant is None or tool.scope not in grant.scopes:
            return DENY, f"scope {tool.scope!r} not granted in {env}"
        if tool.scope in ("read", "notify"):
            return ALLOW, "read-only or notification"
        if tool.risk == "high":
            return APPROVE, "high-risk action"
        if self.autonomy == 0:
            return APPROVE, "autonomy level 0"
        if not tool.reversible and self.autonomy < 2:
            return APPROVE, "irreversible action at autonomy level 1"
        return ALLOW, f"low-risk action at autonomy level {self.autonomy}"
