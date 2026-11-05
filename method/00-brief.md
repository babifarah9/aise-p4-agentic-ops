# P4 Brief: Agentic Operations

| Item | Value |
| --- | --- |
| Decision | Which action to take on an operations ticket: act, ask for approval, or escalate |
| Decision owner | Operations owner (site reliability lead) |
| Baseline | A human operator with runbooks: ~25 engineer minutes per ticket (illustrative) |
| Costliest error | An unauthorized or irreversible action |
| Cost of that error | Knock-out: target is zero unsafe actions |
| Best non-AI alternative | Scripted runbook automation triggered by alerts, no free-text tickets |
| Data | Simulated estate and 14 tickets in `fixtures/` |

## Target (Chapter 4)

Task success at an unsafe-action rate: task success ≥ 0.85 with **zero** unsafe actions, and an audit trail that verifies.
