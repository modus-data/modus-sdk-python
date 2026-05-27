"""
Example: listing agents and their details.

Run with:
    export MODUS_API_KEY=modus_xxx
    python examples/list_agents.py
"""
import modus

client = modus.Modus()

print("=== Agents ===")
agents = list(client.agents.list().auto_paging_iter())

if not agents:
    print("  No agents found.")
else:
    for agent in agents:
        status = "active" if agent.is_active else "draft"
        enabled = "" if agent.is_enabled else "  [disabled]"
        unpublished = "  [unpublished]" if agent.has_unpublished_changes else ""
        print(f"  [{status}] {agent.name}{enabled}{unpublished}")
        print(f"    id={agent.id}  type={agent.type}")
        print(f"    created={agent.created_at.date()}  updated={agent.updated_at.date()}")

print(f"\nTotal: {len(agents)} agent(s).")
