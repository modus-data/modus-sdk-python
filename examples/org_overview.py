"""
Example: get a snapshot of everything in your Modus org.

Shows all skills (active vs draft), all agents, and a context item summary.
Useful as a quick health-check or onboarding script.

Run with:
    export MODUS_API_KEY=modus_xxx
    export MODUS_BASE_URL=https://api.modus.com   # or http://localhost:3040 for local dev
    python examples/org_overview.py
"""

import modus

client = modus.Modus()

# ── Skills ────────────────────────────────────────────────────────────────────

print("=== Skills ===")
active, draft = [], []

for skill in client.skills.list().auto_paging_iter():
    (active if skill.is_active else draft).append(skill)

print(f"  Active ({len(active)}):")
for s in active:
    print(f"    • {s.name}  (id={s.id}, slug={s.slug})")

print(f"  Draft ({len(draft)}):")
for s in draft:
    unpublished = " [unpublished changes]" if s.has_unpublished_changes else ""
    print(f"    • {s.name}{unpublished}  (id={s.id})")

# ── Agents ────────────────────────────────────────────────────────────────────

print("\n=== Agents ===")
all_agents = list(client.agents.list().auto_paging_iter())

if not all_agents:
    print("  No agents found.")
else:
    for agent in all_agents:
        status = "active" if agent.is_active else "draft"
        print(f"  • [{status}] {agent.name}  (type={agent.type}, id={agent.id})")

# ── Context summary ───────────────────────────────────────────────────────────

print("\n=== Context ===")
counts: dict[str, int] = {}

for item in client.context.items.list().auto_paging_iter():
    counts[item.context_type] = counts.get(item.context_type, 0) + 1

if not counts:
    print("  No context items yet.")
else:
    for kind, n in sorted(counts.items()):
        print(f"  {kind}: {n}")
    print("  ──────────────")
    print(f"  Total: {sum(counts.values())}")

# ── Recent conversations (first 3 active skills) ──────────────────────────────

print("\n=== Recent conversations ===")
for skill in active[:3]:
    conv_page = client.skills.conversations.list(skill.id, page_size=3)
    more = " (+ more)" if conv_page.has_next_page() else ""
    print(f"  {skill.name}: {len(conv_page)} recent{more}")
    for conv in conv_page:
        first = conv.first_message or ""
        preview = (first[:60] + "…") if len(first) > 60 else first
        print(f"    thread {conv.thread_id[:8]}…  ({conv.message_count} msgs)  \"{preview}\"")
