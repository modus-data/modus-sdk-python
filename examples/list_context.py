"""
Example: listing and filtering context items.

Run with:
    export MODUS_API_KEY=modus_xxx
    python examples/list_context.py
"""
import modus

client = modus.Modus()

print("=== All context items ===")
all_items = list(client.context.items.list().auto_paging_iter())

if not all_items:
    print("  (none yet)")

counts: dict[str, int] = {}
for item in all_items:
    counts[item.context_type] = counts.get(item.context_type, 0) + 1
    verified = " [verified]" if item.verification_status == "verified" else ""
    label = item.title or item.description or "(no title)"
    print(f"  [{item.context_type}] {label}{verified}")

if counts:
    print("\n=== Summary by type ===")
    for kind, n in sorted(counts.items()):
        print(f"  {kind}: {n}")
    print(f"  Total: {len(all_items)}")

print("\n=== Notes only ===")
notes = list(client.context.items.list(context_type="note").auto_paging_iter())
for item in notes:
    print(f"  {item.title or '(no title)'}  uid={item.uid[:8]}...")
print(f"  {len(notes)} note(s).")
