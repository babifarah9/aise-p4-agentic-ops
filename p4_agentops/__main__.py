"""Command line: `python -m p4_agentops run|compare|gate`."""

from __future__ import annotations

import argparse
import sys

from .evaluate import load_tickets, run


def _summary(name, r) -> str:
    return (f"{name:<22} task success {r.task_success:.2f} | unsafe actions {r.unsafe_actions} | "
            f"autonomous {r.autonomous_share:.0%} | approvals {r.approvals} | "
            f"engineer minutes saved {r.minutes_saved:.0f} | audit {'ok' if r.audit_ok else 'BROKEN'}")


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="p4_agentops", description="P4 agentic operations")
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("run", help="run the ticket set and show each outcome")
    sub.add_parser("compare", help="policy-enforced agent vs the same agent without a policy")
    sub.add_parser("gate", help="fail on any unsafe action or low task success")
    args = p.parse_args(argv)
    tickets = load_tickets()

    if args.cmd == "run":
        r = run(tickets)
        for row in r.rows:
            flag = "ok " if row["ok"] else "BAD"
            print(f"{flag} {row['ticket']}: {row['status']:<10} (expected {row['expected']:<9}) "
                  f"executed={row['executed']} blocked={row['blocked']}" + (f" UNSAFE={row['unsafe']}" if row["unsafe"] else ""))
        print(_summary("policy enforced", r))
        return 0
    if args.cmd == "compare":
        print(_summary("policy enforced", run(tickets, enforce=True)))
        print(_summary("no policy (naive)", run(tickets, enforce=False)))
        return 0
    r = run(tickets)
    print(_summary("policy enforced", r))
    problems = r.gate()
    if problems:
        print("GATE FAILED: " + "; ".join(problems))
        return 1
    print("GATE PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
