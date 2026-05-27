"""
Example: create, update, deploy, and (optionally) delete an agent.

Run with:
    export MODUS_API_KEY=modus_xxx

    python examples/manage_agents.py                    # read-only: lists agents
    python examples/manage_agents.py --write            # creates + updates + deploys (item persists)
    python examples/manage_agents.py --write --delete   # full lifecycle + cleanup at the end

`--write` alone is non-destructive after the run: the agent stays in your org
so you can inspect it. Re-running with `--delete` (and `--write`) tears it
down again. --delete requires --write; passing --delete alone exits immediately
with an error. Use the SPA to clean up agents from previous runs.

Created agents are tagged "[SDK Example]" + a timestamp so they're easy to
find and filter.
"""
import argparse
from datetime import datetime

import modus
from modus.management import ModusManagement

EXAMPLE_PREFIX = "[SDK Example]"


def _example_name() -> str:
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    return f"{EXAMPLE_PREFIX} Daily Revenue Digest {stamp}"


def main(write: bool, delete: bool) -> None:
    if delete and not write:
        raise SystemExit(
            "--delete requires --write (the script only deletes the agent it just "
            "created in this run; use the SPA to clean up older example agents)."
        )

    read = modus.Modus()

    # ── List ──────────────────────────────────────────────────────────────────
    print("=== Agents ===")
    agents = list(read.agents.list().auto_paging_iter())
    for agent in agents:
        status = "active" if agent.is_active else "draft"
        marker = "  <- example" if agent.name.startswith(EXAMPLE_PREFIX) else ""
        print(f"  [{status}] {agent.name}  id={agent.id}  type={agent.type}{marker}")
    print(f"  Total: {len(agents)}")

    if not write:
        print(
            "\nRead-only mode. Pass --write to create + update + deploy a sample "
            "agent (it will persist), or --write --delete to also clean it up."
        )
        return

    mgmt = ModusManagement()

    # ── Create (enriched) ─────────────────────────────────────────────────────
    # Populate description and a manual trigger so the agent is recognisable
    # in the SPA, not just an empty draft. type="task" keeps the surface
    # minimal; "workflow" is also valid but requires workflow_structure.
    name = _example_name()
    print(f"\n=== Creating agent: {name!r} ===")
    created = mgmt.agents.create(
        name=name,
        type="task",
        description=(
            "Sample agent created by the Modus Python SDK example "
            "(examples/manage_agents.py). Safe to delete."
        ),
        trigger={
            "type": "manual",
        },
    )
    agent_id = created.id
    print(f"  id={agent_id}  status={created.status}  type={created.type}")
    if created.description:
        print(f"  description={created.description!r}")

    # ── Update ────────────────────────────────────────────────────────────────
    # Partial update: only changed fields are forwarded; the rest are
    # preserved server-side.
    print("\n=== Updating agent ===")
    updated = mgmt.agents.update(
        agent_id,
        name=f"{name} (updated)",
        description=(
            "Updated description from the SDK example — the agent now also "
            "summarises week-over-week change."
        ),
    )
    print(f"  name={updated.name}")
    print(f"  description={updated.description!r}")

    # ── Deploy ────────────────────────────────────────────────────────────────
    print("\n=== Deploying agent ===")
    deployed = mgmt.agents.deploy(agent_id)
    print(f"  status={deployed.status}")

    if not delete:
        print(
            "\nLeaving the agent in place (no --delete). "
            f"Inspect it in the SPA or fetch it with `read.agents.get({agent_id!r})`."
        )
        return

    # ── Delete ────────────────────────────────────────────────────────────────
    print("\n=== Deleting agent ===")
    mgmt.agents.delete(agent_id)
    print(f"  Deleted agent id={agent_id}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Manage Modus agents")
    parser.add_argument(
        "--write",
        action="store_true",
        help="Enable create + update + deploy. The created agent persists unless --delete is also passed.",
    )
    parser.add_argument(
        "--delete",
        action="store_true",
        help="In addition to --write, delete the created agent at the end of the run.",
    )
    args = parser.parse_args()
    main(args.write, args.delete)
