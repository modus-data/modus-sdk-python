"""
Example: create, update, deploy, and (optionally) delete a skill.

Run with:
    export MODUS_API_KEY=modus_xxx

    python examples/manage_skills.py                    # read-only: lists skills
    python examples/manage_skills.py --write            # creates + updates + deploys (item persists)
    python examples/manage_skills.py --write --delete   # full lifecycle + cleanup at the end

`--write` alone is non-destructive after the run: the skill stays in your org
so you can inspect it. Re-running with `--delete` (and `--write`) tears it
down again. --delete requires --write; passing --delete alone exits immediately
with an error. Use the SPA to clean up skills from previous runs.

Created skills are tagged "[SDK Example]" + a timestamp so they're easy to
find and filter.
"""
import argparse
from datetime import datetime

import modus
from modus.management import ModusManagement

EXAMPLE_PREFIX = "[SDK Example]"


def _example_name() -> str:
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    return f"{EXAMPLE_PREFIX} Revenue Analysis {stamp}"


def main(write: bool, delete: bool) -> None:
    if delete and not write:
        raise SystemExit(
            "--delete requires --write (the script only deletes the skill it just "
            "created in this run; use the SPA to clean up older example skills)."
        )

    read = modus.Modus()

    # ── List ──────────────────────────────────────────────────────────────────
    print("=== Skills ===")
    skills = list(read.skills.list().auto_paging_iter())
    for skill in skills:
        status = "active" if skill.is_active else "draft"
        marker = "  <- example" if skill.name.startswith(EXAMPLE_PREFIX) else ""
        print(f"  [{status}] {skill.name}  id={skill.id}{marker}")
    print(f"  Total: {len(skills)}")

    if not write:
        print(
            "\nRead-only mode. Pass --write to create + update + deploy a sample "
            "skill (it will persist), or --write --delete to also clean it up."
        )
        return

    mgmt = ModusManagement()

    # ── Create (enriched) ────────────────────────────────────────────────────
    # Populate the variation block: description, expected output, instructions,
    # and a model so the resulting skill is actually meaningful — not just a
    # placeholder name.
    name = _example_name()
    print(f"\n=== Creating skill: {name!r} ===")
    created = mgmt.skills.create(
        name=name,
        description=(
            "Sample skill created by the Modus Python SDK example "
            "(examples/manage_skills.py). Safe to delete."
        ),
        expected_output=(
            "A short answer with a single number or list, plus one sentence "
            "explaining how it was computed."
        ),
        instructions=[
            "Answer questions about revenue using the connected data sources.",
            "Always show the SQL you ran in a code block before the answer.",
            "If the question is ambiguous, ask one clarifying question first.",
        ],
        model="gpt-4o",
    )
    skill_id = created.id
    print(f"  id={skill_id}  status={created.status}  slug={created.slug}")
    if created.variation:
        print(f"  model={created.variation.get('model')}")
        instr = created.variation.get("instructions") or []
        print(f"  instructions={len(instr)} item(s)")

    # ── Update ────────────────────────────────────────────────────────────────
    # Demonstrate a partial update: only the fields you pass are changed; the
    # rest of the variation is preserved server-side.
    print("\n=== Updating skill ===")
    updated = mgmt.skills.update(
        skill_id,
        name=f"{name} (updated)",
        instructions=[
            "Answer questions about revenue using the connected data sources.",
            "Always cite the metric or saved query you used.",
            "Round to two decimal places unless the user asks otherwise.",
        ],
    )
    print(f"  name={updated.name}")
    if updated.variation:
        instr = updated.variation.get("instructions") or []
        print(f"  instructions={len(instr)} item(s) (now updated)")

    # ── Deploy ────────────────────────────────────────────────────────────────
    print("\n=== Deploying skill ===")
    deployed = mgmt.skills.deploy(skill_id)
    print(f"  status={deployed.status}")

    if not delete:
        print(
            "\nLeaving the skill in place (no --delete). "
            f"Inspect it in the SPA or fetch it with `read.skills.get({skill_id!r})`."
        )
        return

    # ── Delete ────────────────────────────────────────────────────────────────
    print("\n=== Deleting skill ===")
    mgmt.skills.delete(skill_id)
    print(f"  Deleted skill id={skill_id}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Manage Modus skills")
    parser.add_argument(
        "--write",
        action="store_true",
        help="Enable create + update + deploy. The created skill persists unless --delete is also passed.",
    )
    parser.add_argument(
        "--delete",
        action="store_true",
        help="In addition to --write, delete the created skill at the end of the run.",
    )
    args = parser.parse_args()
    main(args.write, args.delete)
