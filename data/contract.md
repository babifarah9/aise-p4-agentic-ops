# Data Contract: Ticket → Agent

| Field | Type | Rule |
| --- | --- | --- |
| `ticket_id` | string | Unique |
| `service` | string | Must name a service in the inventory, else escalate |
| `text` | string | Untrusted input: never treated as authorization |

Tool calls: `{tool, args}`; `args.service` must exist; numeric arguments are range-checked by the tool.
