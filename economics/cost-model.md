# P4 Cost Model: the Economics of Autonomy

Implemented in `p4_agentops/evaluate.py` with illustrative constants.

```
minutes saved = Σ over tickets closed by the agent (25 − 3 × approvals) − Σ over escalations 2
```

| Constant | Value | Meaning |
| --- | --- | --- |
| `HUMAN_MINUTES` | 25 | Engineer time to handle a ticket by hand |
| `APPROVAL_MINUTES` | 3 | Engineer time to review one approval |
| `ESCALATION_OVERHEAD_MINUTES` | 2 | Extra time when the agent escalates |

More autonomy saves more minutes until an unsafe action happens; one irreversible error in prod outweighs a year of saved minutes, which is why unsafe actions are a knock-out, not a cost line.
