"""Append-only, hash-chained audit log.

Every proposed action, policy decision, approval and result is recorded.
Each record carries the hash of the previous one, so editing or deleting a
past record breaks verification.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field

GENESIS = "0" * 64


@dataclass
class AuditLog:
    records: list[dict] = field(default_factory=list)

    def append(self, **entry) -> dict:
        prev = self.records[-1]["hash"] if self.records else GENESIS
        body = {"seq": len(self.records), "prev": prev, **entry}
        body["hash"] = hashlib.sha256(json.dumps(body, sort_keys=True, default=str).encode()).hexdigest()
        self.records.append(body)
        return body

    def verify(self) -> bool:
        prev = GENESIS
        for i, r in enumerate(self.records):
            body = {k: v for k, v in r.items() if k != "hash"}
            if r["seq"] != i or r["prev"] != prev:
                return False
            if hashlib.sha256(json.dumps(body, sort_keys=True, default=str).encode()).hexdigest() != r["hash"]:
                return False
            prev = r["hash"]
        return True
