"""
Example: listing skills and browsing conversations.

Run with:
    export MODUS_API_KEY=modus_xxx
    export MODUS_BASE_URL=http://localhost:3040   # local dev (modus-api)
    python examples/list_skills.py
"""

import modus

client = modus.Modus()

# ── List all skills ───────────────────────────────────────────────────────────

print("=== Skills ===")
# auto_paging_iter() fetches all pages automatically (20 per request).
skills = list(client.skills.list().auto_paging_iter())

for skill in skills:
    # Status line
    if skill.is_active:
        status = "active"
    elif skill.is_draft:
        status = "draft"
    else:
        status = skill.status

    unpublished = "  [unpublished changes]" if skill.has_unpublished_changes else ""
    print(f"  {skill.name}{unpublished}")
    print(f"    id={skill.id}  slug={skill.slug}  status={status}")
    print(f"    created={skill.created_at.date()}  updated={skill.updated_at.date()}")

print(f"\nTotal: {len(skills)} skill(s).")

# ── Full detail for each skill ────────────────────────────────────────────────
# GET /api/v1/skills/:id returns the variation block with model, instructions,
# connected tools, data connections, sub-skills, and more.

print("\n=== Skill details ===")
for summary in skills:
    skill = client.skills.get(summary.id)
    print(f"\n  ── {skill.name} ──")
    print(f"     Status:   {skill.status}")

    if skill.variation:
        # Model
        model = skill.variation.get("model", "N/A")
        print(f"     Model:    {model}")

        # Instructions
        raw = skill.variation.get("instructions") or []
        instructions = raw if isinstance(raw, str) else [str(i) for i in raw]
        if instructions:
            for idx, inst in enumerate(instructions, 1):
                preview = inst[:80].replace("\n", " ") + ("…" if len(inst) > 80 else "")
                print(f"     Instruction {idx}: {preview}")

        # Connected tools (toolset)
        toolset = skill.variation.get("toolset") or {}
        if toolset:
            print(f"     Tools ({len(toolset)}):")
            for tool_name, tool_cfg in toolset.items():
                if isinstance(tool_cfg, list):
                    # e.g. visualization_creator: ["chartjs", "report_generation"]
                    print(f"       - {tool_name}: {', '.join(str(a) for a in tool_cfg)}")
                elif isinstance(tool_cfg, dict):
                    # e.g. slack: {"actions": ["SendMessage", ...]}
                    actions = tool_cfg.get("actions") or []
                    print(f"       - {tool_name}: {len(actions)} action(s)")
                    if actions:
                        preview_actions = ", ".join(actions[:5])
                        suffix = ", …" if len(actions) > 5 else ""
                        print(f"           ({preview_actions}{suffix})")
                else:
                    print(f"       - {tool_name}")
        else:
            print("     Tools:    (none)")

        # Data connections
        connection_set = skill.variation.get("connectionSet") or []
        if connection_set:
            print(f"     Connections ({len(connection_set)}):")
            for conn in connection_set:
                cid = conn.get("connection_id", "?")
                path = conn.get("path") or []
                label = f"{cid}" + (f"  path={path}" if path else "")
                print(f"       - {label}")
        else:
            print("     Connections: (none)")

        # Sub-skills (agents supervised by this skill)
        sub_ids = skill.variation.get("supervisionSubordinateIds") or []
        if sub_ids:
            print(f"     Sub-skills: {', '.join(str(i) for i in sub_ids)}")

    # Access visibility
    if skill.access_config:
        visibility = skill.access_config.get("visibility", "unknown")
        owner = skill.access_config.get("ownerEmail", "")
        print(f"     Access:   {visibility}" + (f"  (owner: {owner})" if owner else ""))

# ── Conversations per skill ───────────────────────────────────────────────────
# The list endpoint returns lightweight ConversationListItem summaries.
# Call conversations.get(skill_id, thread_id) for the full message history.

print("\n=== Recent conversations ===")
for summary in skills:
    conv_page = client.skills.conversations.list(summary.id, page_size=5)
    more = " (+ more)" if conv_page.has_next_page() else ""
    print(f"\n  {summary.name}: {len(conv_page)} conversation(s){more}")

    for item in conv_page:
        title = item.title or "(untitled)"
        print(f"    [{title}]  thread={item.thread_id[:16]}…  ({item.message_count} messages)")
        if item.first_message:
            preview = item.first_message[:80].replace("\n", " ")
            if len(item.first_message) > 80:
                preview += "…"
            print(f"      started: \"{preview}\"")
        print(f"      updated: {item.updated_at.strftime('%Y-%m-%d %H:%M')}")

# ── Fetch full history for the first available thread ────────────────────────
# Demonstrates conversations.get() which returns the complete message list.

print("\n=== Full thread detail (first available) ===")
found = False
for summary in skills:
    conv_page = client.skills.conversations.list(summary.id, page_size=1)
    if conv_page.items:
        item = conv_page.items[0]
        conv = client.skills.conversations.get(summary.id, item.thread_id)
        print(f"  Skill:    {summary.name}")
        print(f"  Thread:   {conv.thread_id}")
        print(f"  Messages: {len(conv.messages)}")
        for msg in conv.messages[:4]:   # show first 4 turns
            msg_type = msg.type or "unknown"
            text = (msg.content or "").replace("\n", " ")[:80]
            suffix = "…" if len(msg.content or "") > 80 else ""
            tools = ""
            if msg.tool_calls:
                tool_names = [tc.get("name", "?") for tc in msg.tool_calls]
                tools = f"  [tools: {', '.join(tool_names[:3])}]"
            print(f"    [{msg_type}] {text}{suffix}{tools}")
        if len(conv.messages) > 4:
            print(f"    … ({len(conv.messages) - 4} more messages)")
        found = True
        break
if not found:
    print("  (no conversations found)")
