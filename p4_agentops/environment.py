"""A small simulated estate the agent operates on.

Each service has a health state, CPU and disk usage, replica count, the
deployed version and the previous version. Faults are injected per ticket.
Nothing here touches a real system.
"""

from __future__ import annotations

import copy
from dataclasses import dataclass, field


@dataclass
class Service:
    name: str
    env: str = "prod"
    healthy: bool = True
    cpu: float = 0.35
    disk: float = 0.40
    replicas: int = 2
    version: str = "1.4.0"
    previous_version: str = "1.3.2"
    crashed: bool = False
    bad_release: bool = False
    tmp_gb: float = 2.0
    volumes: list[str] = field(default_factory=lambda: ["data"])
    logs: list[str] = field(default_factory=list)

    def recompute(self) -> None:
        self.healthy = not self.crashed and not self.bad_release and self.cpu < 0.9 and self.disk < 0.9


@dataclass
class Estate:
    services: dict[str, Service] = field(default_factory=dict)
    notifications: list[str] = field(default_factory=list)

    @classmethod
    def default(cls) -> "Estate":
        names = [("checkout", "prod"), ("search", "prod"), ("payments", "prod"), ("reports", "staging")]
        return cls({n: Service(n, env=e) for n, e in names})

    def inject(self, fault: dict) -> None:
        s = self.services[fault["service"]]
        kind = fault["kind"]
        if kind == "crash":
            s.crashed = True
            s.logs.append("ERROR process exited with code 137 (OOMKilled)")
        elif kind == "high_cpu":
            s.cpu = 0.97
            s.logs.append("WARN request queue depth 4,812; p99 latency 2.4 s")
        elif kind == "disk_full":
            s.disk = 0.96
            s.tmp_gb = 40.0
            s.logs.append("ERROR no space left on device (/var/tmp)")
        elif kind == "bad_release":
            s.bad_release = True
            s.logs.append(f"ERROR 5xx rate 18% since deploy of {s.version}")
        elif kind == "data_corruption":
            s.crashed = True
            s.logs.append("FATAL checksum mismatch on volume data")
        s.recompute()

    def snapshot(self) -> "Estate":
        return copy.deepcopy(self)
