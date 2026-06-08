"""
Manage skills with modus.management.ModusManagement().

Read-only by default. Pass --write to create, update, and deploy a sample skill;
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
    print("=== Skills ===")
    skills = list(read.skills.list().auto_paging_iter())
    for skill in skills:
        status = "active" if skill.is_active else "draft"
        marker = "  <- example" if skill.name.startswith(EXAMPLE_PREFIX) else ""
        print(f"  [{status}] {skill.name}  id={skill.id}{marker}")

    if not write:
        print("\nRead-only. Pass --write to create + deploy a sample skill.")
        return

    mgmt = ModusManagement()
    name = _example_name()
    print(f"\n=== Creating skill: {name!r} ===")
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
    created = mgmt.skills.create(
        name=name,
        description="Sample skill from manage_skill.py. Safe to delete.",
        instructions=["Answer revenue questions using connected data sources."],
        model="gpt-4o",
        toolset=toolset,
    )
    skill_id = created.id
    print(f"  id={skill_id}  status={created.status}")

    print("\n=== Deploying skill ===")
    deployed = mgmt.skills.deploy(skill_id)
    print(f"  status={deployed.status}")

    if delete:
        print("\n=== Deleting skill ===")
        mgmt.skills.delete(skill_id)
        print(f"  deleted id={skill_id}")
    else:
        print("\nSkill left in place. Re-run with --write --delete to clean up.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Manage Modus skills")
    parser.add_argument(
        "--write",
        action="store_true",
        help="Create and deploy a sample skill.",
    )
    parser.add_argument(
        "--delete",
        action="store_true",
        help="With --write, delete the skill created in this run.",
    )
    args = parser.parse_args()
    main(args.write, args.delete)
