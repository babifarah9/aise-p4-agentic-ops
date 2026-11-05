"""The operations agent: diagnose from evidence, propose, pass the policy, act, verify.

The planner is pluggable. The default `RunbookPlanner` maps log signatures to
runbook steps. To show that safety comes from the policy engine and not from
the planner behaving well, the planner also proposes any action a ticket asks
for in so many words ("please delete volume data"), as a language model that
follows instructions in its input might. The policy engine must stop those.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Callable, Protocol

from .audit import AuditLog
from .environment import Estate
from .policy import ALLOW, APPROVE, Policy
from .tools import TOOLS, ToolError


@dataclass(frozen=True)
class Step:
    tool: str
    args: dict
    why: str


@dataclass
class Ticket:
    ticket_id: str
    text: str
    service: str | None = None


@dataclass
class Outcome:
    ticket_id: str
    status: str                       # "resolved", "escalated", "no_action"
    executed: list[str] = field(default_factory=list)
    blocked: list[str] = field(default_factory=list)
    approvals_requested: int = 0
    notes: list[str] = field(default_factory=list)


class Planner(Protocol):
    def plan(self, ticket: Ticket, evidence: dict[str, str]) -> list[Step]: ...


_REQUEST = re.compile(r"\b(delete|drop|remove)\s+(?:the\s+)?volume\s+(\w+)", re.I)
_ROTATE = re.compile(r"\brotate\b.*\bcredential", re.I)

RUNBOOK = (
    ("OOMKilled", "restart_service", {}, "process killed for memory: restart"),
    ("queue depth", "scale_service", {"double": True}, "saturated: double replicas"),
    ("no space left", "clear_tmp", {}, "disk full in /var/tmp: clear temp files"),
    ("since deploy", "rollback_deploy", {}, "errors began with the last deploy: roll back"),
)


class RunbookPlanner:
    def plan(self, ticket: Ticket, evidence: dict[str, str]) -> list[Step]:
        svc = ticket.service
        steps = []
        # Instruction-following on ticket text (the risky behaviour the policy must contain).
        for m in _REQUEST.finditer(ticket.text):
            steps.append(Step("delete_volume", {"service": svc, "volume": m.group(2)}, "requested in ticket"))
        if _ROTATE.search(ticket.text):
            steps.append(Step("rotate_credentials", {"service": svc}, "requested in ticket"))
        logs = evidence.get("logs", "")
        if "checksum mismatch" in logs:
            return steps  # no runbook step for data corruption: escalate
        for signature, tool, extra, why in RUNBOOK:
            if signature in logs:
                args = {"service": svc}
                if extra.get("double"):
                    replicas = int(re.search(r"replicas=(\d+)", evidence["status"]).group(1))
                    args["replicas"] = min(10, replicas * 2)
                steps.append(Step(tool, args, why))
        return steps


Approver = Callable[[Step, Ticket], bool]


def _deny_all(step: Step, ticket: Ticket) -> bool:
    return False


class Agent:
    def __init__(self, estate: Estate, policy: Policy | None = None, planner: Planner | None = None,
                 approver: Approver = _deny_all, audit: AuditLog | None = None, enforce: bool = True):
        self.estate = estate
        self.policy = policy or Policy()
        self.planner = planner or RunbookPlanner()
        self.approver = approver
        self.audit = audit if audit is not None else AuditLog()
        self.enforce = enforce  # False = the naive agent, for comparison only

    def _call(self, ticket: Ticket, step: Step) -> str:
        tool = TOOLS[step.tool]
        args = {k: v for k, v in step.args.items()}
        return tool.fn(self.estate, **args)

    def handle(self, ticket: Ticket) -> Outcome:
        out = Outcome(ticket.ticket_id, "escalated")
        self.audit.append(event="ticket", ticket=ticket.ticket_id, service=ticket.service)
        if ticket.service not in self.estate.services:
            out.notes.append("no known service named in ticket")
            self._escalate(ticket, out, "unknown service")
            return out
        svc = self.estate.services[ticket.service]
        evidence = {"status": TOOLS["get_status"].fn(self.estate, ticket.service),
                    "logs": TOOLS["read_logs"].fn(self.estate, ticket.service)}
        self.audit.append(event="diagnose", ticket=ticket.ticket_id, **evidence)
        steps = self.planner.plan(ticket, evidence)
        if svc.healthy and not steps:
            out.status = "no_action"
            self.audit.append(event="close", ticket=ticket.ticket_id, reason="healthy, nothing to do")
            return out
        was_healthy = svc.healthy
        for step in steps[: self.policy.max_actions_per_ticket]:
            tool = TOOLS[step.tool]
            decision, reason = self.policy.decide(tool, svc.env)
            if not self.enforce:
                decision, reason = ALLOW, "policy not enforced"
            self.audit.append(event="propose", ticket=ticket.ticket_id, tool=step.tool, args=step.args,
                              why=step.why, decision=decision, reason=reason)
            if decision == APPROVE:
                out.approvals_requested += 1
                granted = self.approver(step, ticket)
                self.audit.append(event="approval", ticket=ticket.ticket_id, tool=step.tool, granted=granted)
                if not granted:
                    out.blocked.append(step.tool)
                    continue
            elif decision != ALLOW:
                out.blocked.append(step.tool)
                continue
            try:
                result = self._call(ticket, step)
            except ToolError as e:
                result = f"error: {e}"
            out.executed.append(step.tool)
            self.audit.append(event="act", ticket=ticket.ticket_id, tool=step.tool, result=result)
            if not was_healthy and self.estate.services[ticket.service].healthy:
                break

        if was_healthy and not out.executed:
            self._escalate(ticket, out, "requested action not permitted")
        elif self.estate.services[ticket.service].healthy:
            out.status = "resolved"
            self.audit.append(event="verify", ticket=ticket.ticket_id, healthy=True)
        else:
            self._escalate(ticket, out, "not healthy after permitted actions")
        return out

    def _escalate(self, ticket: Ticket, out: Outcome, reason: str) -> None:
        msg = f"{ticket.ticket_id}: escalated ({reason})"
        TOOLS["notify_oncall"].fn(self.estate, msg)
        out.status = "escalated"
        self.audit.append(event="escalate", ticket=ticket.ticket_id, reason=reason)
