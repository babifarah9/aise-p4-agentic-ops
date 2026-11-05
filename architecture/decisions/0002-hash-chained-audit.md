# ADR 0002: Hash-chained audit log

**Status:** accepted

**Decision.** Every ticket, diagnosis, proposal, policy decision, approval, action and escalation is appended to a log in which each record carries the previous record's SHA-256.

**Consequences.** Tampering is detectable by `AuditLog.verify()`. In production, anchor the latest hash in an external write-once store.
