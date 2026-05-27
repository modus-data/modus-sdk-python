"""
Example: syncing a set of business definitions to Modus context.

A common automation pattern: you maintain a source of truth (a dict, a YAML file,
a database) and want to keep the Modus context in sync — creating items that don't
exist yet and updating ones that have changed.

Run with:
    export MODUS_API_KEY=modus_xxx
    python examples/sync_knowledge.py
"""

import modus
from modus.management import ModusManagement

read = modus.Modus()
mgmt = ModusManagement()

# ── Your source of truth ──────────────────────────────────────────────────────

DEFINITIONS = {
    "Fiscal Year":
        "Our fiscal year runs February 1 through January 31.",
    "ARR":
        "Annual Recurring Revenue: total contracted recurring revenue annualised. "
        "Excludes one-time fees and professional services.",
    "MQL":
        "Marketing Qualified Lead: a lead that marketing has determined is ready "
        "to be handed to sales based on engagement score >= 50.",
    "NPS":
        "Net Promoter Score: (% promoters) - (% detractors), surveyed quarterly. "
        "Promoters score 9-10, detractors score 0-6.",
}

# ── Fetch what's already in Modus ─────────────────────────────────────────────

print("=== Fetching existing context items ===")
existing: dict[str, modus.ContextItem] = {}

for item in read.context.items.list(context_type="note").auto_paging_iter():
    existing[item.title] = item

print(f"  Found {len(existing)} existing notes.")

# ── Sync: create missing, update changed ─────────────────────────────────────

print("\n=== Syncing definitions ===")
created_count = 0
updated_count = 0

for title, content in DEFINITIONS.items():
    try:
        if title not in existing:
            mgmt.context.create_note(title=title, content=content)
            print(f"  + Created  '{title}'")
            created_count += 1
        else:
            item = existing[title]
            if item.content == content:
                print(f"  = Skipped  '{title}'  (unchanged)")
            else:
                mgmt.context.items.update(item.uid, content=content, description="Synced from DEFINITIONS.")
                print(f"  ~ Updated  '{title}'")
                updated_count += 1
    except modus.InternalServerError:
        print(f"  ✗ Skipped  '{title}'  (backend error — notes require S3, check local dev setup)")

print(f"\n  Created: {created_count}")
print(f"  Updated: {updated_count}")

# ── Final state ───────────────────────────────────────────────────────────────

print("\n=== Context notes after sync ===")
for item in read.context.items.list(context_type="note").auto_paging_iter():
    verified = " ✓" if item.verification_status == "verified" else ""
    label = item.title or item.description or "(no title)"
    print(f"  [{item.uid[:8]}...] {label}{verified}")
