"""
Quickstart: list scopes and org context with modus.Modus().

Modus is your organization's context layer — curated knowledge about your
data, metrics, and workflows (warehouses, dashboards, saved queries) that
scopes and workflows use when answering questions about revenue, ARR, and more.

For a full analyst-style conversation, run modus_chat.py next.

Setup:
    export MODUS_API_KEY=modus_xxx
    python examples/scripts/quickstart.py
"""

import os
import sys

import modus


def main() -> None:
    if not os.environ.get("MODUS_API_KEY"):
        sys.exit(
            "Export MODUS_API_KEY before running:\n"
            "  export MODUS_API_KEY=modus_xxx"
        )

    client = modus.Modus()

    print("=== Scopes ===")
    for scope in client.scopes.list().auto_paging_iter():
        print(f"  {scope.name}  ({scope.status})")

    print("\n=== Context (sample) ===")
    print("  (tables, metrics, and notes Modus can compose for revenue / ARR questions)")
    page = client.context.items.list(page_size=5)
    if not page.items:
        print("  No context items yet.")
        return
    for item in page:
        print(f"  [{item.context_type}] {modus.context_item_label(item)}")


if __name__ == "__main__":
    main()
