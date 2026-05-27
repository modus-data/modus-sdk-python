"""
Manage context items — list, create (enriched), update, optionally delete.

Run with:
    export MODUS_API_KEY=modus_xxx
    export MODUS_BASE_URL=http://localhost:3040   # local dev

    python examples/manage_context.py                    # read-only
    python examples/manage_context.py --write            # creates + updates (items persist)
    python examples/manage_context.py --write --delete   # full lifecycle + cleanup at end

`--write` alone is non-destructive after the run: the context items stay in
your org so you can inspect them. Re-run with `--write --delete` to also
clean them up. `--delete` without `--write` is rejected — the script doesn't
track state across runs, so use the SPA or `client.context.items.delete(uid)`
to clean up older example items.

This example demonstrates two context types:

  - **Note** — markdown text.
  - **Link** — URL extraction.

`create_saved_query` is intentionally NOT demonstrated here. It works
end-to-end on the backend, but it requires a `connection_id` UUID and
there is no public way to enumerate connections through the SDK or
OpenAPI today. Once `client.connections.list()` ships (tracked in
docs/DEVELOPMENT.md → "Public connection discovery"), the saved-query
step will be added back. The four stub creators (dimensions, facts,
metrics, filters) are also not exercised — they raise NotImplementedError
until the backend ships real persistence.

Notes and links will be skipped (with a clear message) if your local stack
hasn't wired up S3 yet.

Created items have "[SDK Example]" in the title so they're easy to find.
"""
import argparse
from datetime import datetime
from typing import List, Optional

import modus
from modus.management import ModusManagement

EXAMPLE_PREFIX = "[SDK Example]"


def _stamp() -> str:
    return datetime.now().strftime("%Y%m%d-%H%M%S")


def main(write: bool, delete: bool) -> None:
    if delete and not write:
        raise SystemExit(
            "--delete requires --write (the script only deletes the items it just "
            "created in this run; use the SPA or client.context.items.delete(uid) "
            "to clean up older example items)."
        )

    read = modus.Modus()

    # ── List ──────────────────────────────────────────────────────────────────
    print("=== Context items ===")
    page = read.context.items.list(limit=10)
    if not page.items:
        print("  (none yet)")
    for item in page:
        verified = " [verified]" if item.verification_status == "verified" else ""
        label = item.title or item.description or "(no title)"
        marker = "  <- example" if (item.title or "").startswith(EXAMPLE_PREFIX) else ""
        print(f"  [{item.context_type}] {label}{verified}  uid={item.uid[:8]}...{marker}")

    if not write:
        print(
            "\nRead-only mode. Pass --write to create sample items "
            "(they will persist), or --write --delete to also clean them up."
        )
        return

    mgmt = ModusManagement()
    created_uids: List[str] = []
    note_uid: Optional[str] = None

    # ── Create: a markdown note ───────────────────────────────────────────────
    # Enriched body (multi-paragraph markdown) so it actually looks like
    # something a user would store, not just a placeholder.
    note_title = f"{EXAMPLE_PREFIX} Fiscal Year Definition {_stamp()}"
    note_content = (
        "# Fiscal Year Definition\n"
        "\n"
        "Our fiscal year runs **February 1 - January 31**.\n"
        "\n"
        "## Quarters\n"
        "\n"
        "- Q1: Feb - Apr\n"
        "- Q2: May - Jul\n"
        "- Q3: Aug - Oct\n"
        "- Q4: Nov - Jan\n"
        "\n"
        "_Created by the Modus Python SDK example. Safe to delete._\n"
    )

    print(f"\n=== Creating note: {note_title!r} ===")
    try:
        note = mgmt.context.create_note(title=note_title, content=note_content)
        note_uid = note.context_item_id
        created_uids.append(note_uid)
        print(f"  kind={note.kind}  uid={note_uid}")
    except modus.InternalServerError as exc:
        # Notes write through to S3 — local stacks without LocalStack S3
        # wired up will fail here. Surface a clean message and continue.
        print(f"  Skipped note — {exc}")
        print("  (notes require S3; wire LocalStack or run against staging)")

    # ── Create: a link (URL extraction) ───────────────────────────────────────
    # The backend extracts the page content; pass a stable, public URL so the
    # example is reproducible.
    link_url = "https://docs.python.org/3/library/json.html"
    link_title = f"{EXAMPLE_PREFIX} Python json module docs {_stamp()}"
    print(f"\n=== Creating link: {link_url} ===")
    try:
        link = mgmt.context.create_link(
            url=link_url,
            title=link_title,
            is_crawl=False,
        )
        link_uid = link.context_item_id
        created_uids.append(link_uid)
        print(f"  kind={link.kind}  uid={link_uid}")
    except modus.InternalServerError as exc:
        # Link extraction also writes to S3 and may hit external network.
        print(f"  Skipped link — {exc}")
    except modus.ModusError as exc:
        print(f"  Skipped link — {exc.status_code}: {exc.message}")

    if not created_uids:
        print(
            "\nNothing was created — see the messages above. Nothing to update or delete."
        )
        return

    # ── Get + Update (note only) ──────────────────────────────────────────────
    if note_uid is not None:
        print("\n=== Fetching note ===")
        item = read.context.items.get(note_uid)
        print(f"  title={item.title}  type={item.context_type}")

        print("\n=== Updating note description ===")
        updated = mgmt.context.items.update(
            note_uid,
            description="Updated by the SDK example — adds explicit Q4 boundaries.",
        )
        print(f"  description={updated.description!r}")

    if not delete:
        print("\nLeaving items in place (no --delete). Created uids:")
        for uid in created_uids:
            print(f"  - {uid}")
        print(
            "Re-run with --write --delete, or call "
            "`mgmt.context.items.delete(uid)` to remove them."
        )
        return

    # ── Delete ────────────────────────────────────────────────────────────────
    print("\n=== Deleting created items ===")
    for uid in created_uids:
        deletion = mgmt.context.items.delete(uid)
        print(f"  deleted={deletion.deleted}  uid={deletion.uid}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Manage Modus context items")
    parser.add_argument(
        "--write",
        action="store_true",
        help="Enable create + update. The created items persist unless --delete is also passed.",
    )
    parser.add_argument(
        "--delete",
        action="store_true",
        help="In addition to --write, delete the items created during this run.",
    )
    args = parser.parse_args()
    main(args.write, args.delete)
