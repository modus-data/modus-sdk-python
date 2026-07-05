"""
Manage scopes with modus.management.ModusManagement().

Read-only by default. Pass --write to create, update, and deploy a sample scope;
add --delete to remove it at the end of the run.

Setup:
    export MODUS_API_KEY=modus_xxx
    python examples/scripts/manage_skill.py
    python examples/scripts/manage_skill.py --write
    python examples/scripts/manage_skill.py --write --delete
"""

from __future__ import annotations

import argparse
import os
import sys
from datetime import datetime

import modus
from modus.management import ModusManagement, Toolset

EXAMPLE_PREFIX = "[SDK Example]"


def _example_name() -> str:
    return f"{EXAMPLE_PREFIX} Revenue Analysis {datetime.now():%Y%m%d-%H%M%S}"


def main(write: bool, delete: bool) -> None:
    if not os.environ.get("MODUS_API_KEY"):
        sys.exit(
            "Export MODUS_API_KEY before running:\n"
            "  export MODUS_API_KEY=modus_xxx"
        )
    if delete and not write:
        sys.exit("--delete requires --write.")

    read = modus.Modus()
    print("=== Scopes ===")
    scopes = list(read.scopes.list().auto_paging_iter())
    for scope in scopes:
        status = "active" if scope.status == "active" else "draft"
        marker = "  <- example" if scope.name.startswith(EXAMPLE_PREFIX) else ""
        print(f"  [{status}] {scope.name}  id={scope.id}{marker}")

    if not write:
        print("\nRead-only. Pass --write to create + deploy a sample scope.")
        return

    mgmt = ModusManagement()
    name = _example_name()
    print(f"\n=== Creating scope: {name!r} ===")
    # The SQL selector points at a specific connection/schema that won't exist in
    # most orgs, so it's opt-in: set MODUS_SQL_SELECTOR to enable the SQL tool.
    sql_selector = os.environ.get("MODUS_SQL_SELECTOR")
    if sql_selector:
        toolset = Toolset.combine(
            Toolset.sql_runner([sql_selector]),
            Toolset.memory(),
        )
    else:
        toolset = Toolset.memory()
    created = mgmt.scopes.create(
        name=name,
        description=(
            "Sample revenue & ARR analyst scope from manage_skill.py. Safe to delete."
        ),
        instructions=[
            "You are a revenue analyst. Answer questions about ARR, revenue, and growth using org context and connected data.",
            "Cite the tables or queries you rely on when possible.",
        ],
        model="claude-sonnet-5",
        toolset=toolset,
        guardrails=["no-pii"],
    )
    scope_id = created.id
    print(f"  id={scope_id}  status={created.status}")

    print("\n=== Deploying scope ===")
    deployed = mgmt.scopes.deploy(scope_id)
    print(f"  status={deployed.status}")

    if delete:
        print("\n=== Deleting scope ===")
        mgmt.scopes.delete(scope_id)
        print(f"  deleted id={scope_id}")
    else:
        print("\nScope left in place. Re-run with --write --delete to clean up.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Manage Modus scopes")
    parser.add_argument(
        "--write",
        action="store_true",
        help="Create and deploy a sample scope.",
    )
    parser.add_argument(
        "--delete",
        action="store_true",
        help="With --write, delete the scope created in this run.",
    )
    args = parser.parse_args()
    main(args.write, args.delete)
