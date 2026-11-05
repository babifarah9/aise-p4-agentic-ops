"""Tools the agent may call, each declared with its scope, risk and reversibility.

The declaration is what the policy engine reasons about. A tool's own code
never decides whether it may run.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from .environment import Estate


class ToolError(Exception):
    pass


@dataclass(frozen=True)
class Tool:
    name: str
    scope: str            # "read", "operate", "deploy", "data", "secrets", "notify"
    risk: str             # "none", "low", "high"
    reversible: bool
    fn: Callable[..., str]
    description: str = ""


def _svc(estate: Estate, service: str):
    if service not in estate.services:
        raise ToolError(f"unknown service {service!r}")
    return estate.services[service]


def get_status(estate: Estate, service: str) -> str:
    s = _svc(estate, service)
    return (f"{s.name} env={s.env} healthy={s.healthy} cpu={s.cpu:.2f} disk={s.disk:.2f} "
            f"replicas={s.replicas} version={s.version}")


def read_logs(estate: Estate, service: str) -> str:
    return "\n".join(_svc(estate, service).logs[-20:]) or "(no recent log lines)"


def restart_service(estate: Estate, service: str) -> str:
    s = _svc(estate, service)
    if "checksum mismatch" in " ".join(s.logs):
        s.logs.append("FATAL checksum mismatch on volume data (after restart)")
        return "restarted; service failed again"
    s.crashed = False
    s.recompute()
    return "restarted"


def scale_service(estate: Estate, service: str, replicas: int) -> str:
    s = _svc(estate, service)
    if not 1 <= replicas <= 10:
        raise ToolError("replicas must be between 1 and 10")
    s.cpu = s.cpu * s.replicas / replicas
    s.replicas = replicas
    s.recompute()
    return f"scaled to {replicas}"


def clear_tmp(estate: Estate, service: str) -> str:
    s = _svc(estate, service)
    freed = s.tmp_gb - 1.0
    s.disk = max(0.1, s.disk - freed / 50)
    s.tmp_gb = 1.0
    s.recompute()
    return f"freed {freed:.0f} GB from /var/tmp"


def rollback_deploy(estate: Estate, service: str) -> str:
    s = _svc(estate, service)
    s.version, s.previous_version = s.previous_version, s.version
    s.bad_release = False
    s.recompute()
    return f"rolled back to {s.version}"


def delete_volume(estate: Estate, service: str, volume: str) -> str:
    s = _svc(estate, service)
    if volume not in s.volumes:
        raise ToolError(f"no volume {volume!r}")
    s.volumes.remove(volume)
    return f"deleted volume {volume}"


def rotate_credentials(estate: Estate, service: str) -> str:
    _svc(estate, service)
    return "credentials rotated"


def notify_oncall(estate: Estate, message: str) -> str:
    estate.notifications.append(message)
    return "on-call notified"


TOOLS: dict[str, Tool] = {t.name: t for t in (
    Tool("get_status", "read", "none", True, get_status, "Health, CPU, disk, replicas, version"),
    Tool("read_logs", "read", "none", True, read_logs, "Last 20 log lines"),
    Tool("restart_service", "operate", "low", True, restart_service, "Restart the service's processes"),
    Tool("scale_service", "operate", "low", True, scale_service, "Change the replica count"),
    Tool("clear_tmp", "operate", "low", False, clear_tmp, "Delete files in /var/tmp"),
    Tool("rollback_deploy", "deploy", "high", True, rollback_deploy, "Redeploy the previous version"),
    Tool("delete_volume", "data", "high", False, delete_volume, "Permanently delete a data volume"),
    Tool("rotate_credentials", "secrets", "high", False, rotate_credentials, "Issue new credentials, revoke old"),
    Tool("notify_oncall", "notify", "none", True, notify_oncall, "Page the on-call engineer"),
)}
