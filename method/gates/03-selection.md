# Gate: Selection (autonomy level)

Measured on the 14-ticket set (`python -m p4_agentops` with `Policy(autonomy=n)`). The simulated approver grants only the approvals each ticket lists, so routine steps that need approval at low autonomy go unapproved and escalate.

| Level | Acts alone on | Task success | Approvals asked | Engineer minutes saved | Unsafe actions |
| --- | --- | --- | --- | --- | --- |
| 0 | Nothing (suggest only) | 0.50 | 11 | 47 | 0 |
| 1 | Low-risk reversible | 0.79 | 6 | 155 | 0 |
| 2 | Low-risk, including temp cleanup | 1.00 | 3 | 236 | 0 |
| No policy | Everything | 0.64 | 0 | 296 | 6 (knocked out) |

Decision: autonomy level 2, with approval for every high-risk action.
