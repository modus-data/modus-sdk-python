"""
Quickstart: list skills and context with modus.Modus().

Modus is your organization's context layer: curated knowledge about your data,
systems, and workflows that skills and agents use at runtime.

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

    print("=== Skills ===")
    for skill in client.skills.list().auto_paging_iter():
        print(f"  {skill.name}  ({skill.status})")

    print("\n=== Context (sample) ===")
    page = client.context.items.list(page_size=5)
    if not page.items:
        print("  No context items yet.")
        return
    for item in page:
        label = item.title or item.description or item.uid[:8]
        print(f"  [{item.context_type}] {label}")


if __name__ == "__main__":
    main()
