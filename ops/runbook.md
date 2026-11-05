# Runbook: Operating the Agent

| Situation | Action |
| --- | --- |
| Agent proposes a high-risk action | Approver reviews the diagnosis in the audit log before granting |
| Audit verification fails | Stop the agent (autonomy 0), preserve the log, open a security incident |
| New tool added | Declare scope, risk, reversibility; add a policy test and a ticket to the eval set |
| Unsafe action found in review | Knock-out: drop to autonomy 0 until the gate passes on a ticket reproducing it |
