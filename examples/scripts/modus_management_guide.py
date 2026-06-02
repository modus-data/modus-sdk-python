# %% [markdown]
"""
# Modus Management SDK Guide

Configure your Modus org with ``modus.management.ModusManagement()`` (modus-sdk 0.1.3+).

**Consumption vs management:**
- ``modus.Modus()`` — list identity rows, invoke chat/stream, read context
- ``ModusManagement()`` — create/update/deploy/delete skills & agents, write context

**PAT scopes:** ``skills:write``, ``agents:write``, ``context:write`` (+ read scopes).

**Setup:** export ``MODUS_API_KEY`` in your shell (Settings → API Tokens in the Modus app).

**Writes are opt-in:** set ``RUN_WRITES = True`` in the setup cell to create resources.
Set ``CLEANUP = True`` to delete only what this notebook creates in the same run.
"""

# %%
import os
from datetime import datetime
from importlib.metadata import version

import modus
from modus.management import AgentTrigger, MemorySearchRequest, ModusManagement, Toolset

RUN_WRITES = False  # set True to create/update/deploy resources
CLEANUP = False     # set True with RUN_WRITES to delete created resources

EXAMPLE_PREFIX = "[SDK Example]"


def _stamp() -> str:
    return datetime.now().strftime("%Y%m%d-%H%M%S")


print(f"modus-sdk {version('modus-sdk')}")
print(f"MODUS_API_KEY set: {bool(os.environ.get('MODUS_API_KEY'))}")
print(f"RUN_WRITES={RUN_WRITES}  CLEANUP={CLEANUP}")

if not os.environ.get("MODUS_API_KEY"):
    raise SystemExit(
        "Export MODUS_API_KEY before running this guide:\n"
        "  export MODUS_API_KEY=modus_xxx"
    )

read = modus.Modus()
mgmt = ModusManagement()
created: dict[str, object] = {}


# %% [markdown]
"""
## Read via management client

``ModusManagement().skills.get()`` returns the full variation block (instructions,
model, toolset) — richer than the consumption list row.
"""

# %%
print("=== Skills (consumption list) ===")
skills = list(read.skills.list().auto_paging_iter())
for skill in skills:
    status = "active" if skill.is_active else "draft"
    marker = "  <- example" if skill.name.startswith(EXAMPLE_PREFIX) else ""
    print(f"  [{status}] {skill.name}  id={skill.id}{marker}")

if skills:
    sample = skills[0]
    detail = mgmt.skills.get(sample.id)
    print(f"\n=== Management get: {detail.name} ===")
    print(f"  status={detail.status}")
    if detail.model or detail.instructions:
        print(f"  model={detail.model}")
        print(f"  instructions={len(detail.instructions or [])} item(s)")


# %% [markdown]
"""
## Skill lifecycle (create → update → deploy → delete)

Requires ``RUN_WRITES = True``. Created skills are tagged ``[SDK Example]`` + timestamp.
"""

# %%
if not RUN_WRITES:
    print("Read-only — set RUN_WRITES = True to create a sample skill.")
else:
    name = f"{EXAMPLE_PREFIX} Revenue Analysis {_stamp()}"
    print(f"=== Creating skill: {name!r} ===")
    created_skill = mgmt.skills.create(
        name=name,
        description="Sample skill from modus_management_guide.py. Safe to delete.",
        expected_output="A short answer with one supporting sentence.",
        instructions=[
            "Answer revenue questions using connected data sources.",
            "Show the SQL you ran before the answer.",
        ],
        model="gpt-4o",
        toolset=Toolset.model_validate({"sql": {"enabled": True}}),
    )
    created["skill_id"] = created_skill.id
    print(f"  id={created_skill.id}  status={created_skill.status}  slug={created_skill.slug}")

    print("\n=== Updating skill ===")
    updated = mgmt.skills.update(
        created_skill.id,
        name=f"{name} (updated)",
        instructions=[
            "Answer revenue questions using connected data sources.",
            "Cite the metric or saved query you used.",
        ],
    )
    print(f"  name={updated.name}")

    print("\n=== Deploying skill ===")
    deployed = mgmt.skills.deploy(created_skill.id)
    print(f"  status={deployed.status}")


# %% [markdown]
"""
## Agent lifecycle

``AgentTrigger.manual()`` for a task agent. Workflow agents need ``workflow_structure``.
"""

# %%
print("=== Agents (consumption list) ===")
agents = list(read.agents.list().auto_paging_iter())
for agent in agents:
    status = "active" if agent.is_active else "draft"
    marker = "  <- example" if agent.name.startswith(EXAMPLE_PREFIX) else ""
    print(f"  [{status}] {agent.name}  id={agent.id}  type={agent.type}{marker}")

if not RUN_WRITES:
    print("\nRead-only — set RUN_WRITES = True to create a sample agent.")
else:
    agent_name = f"{EXAMPLE_PREFIX} Daily Digest {_stamp()}"
    print(f"\n=== Creating agent: {agent_name!r} ===")
    created_agent = mgmt.agents.create(
        name=agent_name,
        type="task",
        description="Sample agent from modus_management_guide.py. Safe to delete.",
        trigger=AgentTrigger.manual(),
    )
    created["agent_id"] = created_agent.id
    print(f"  id={created_agent.id}  status={created_agent.status}  type={created_agent.type}")

    print("\n=== Updating agent ===")
    updated_agent = mgmt.agents.update(
        created_agent.id,
        name=f"{agent_name} (updated)",
        description="Updated description from the management guide.",
    )
    print(f"  name={updated_agent.name}")

    print("\n=== Deploying agent ===")
    deployed_agent = mgmt.agents.deploy(created_agent.id)
    print(f"  status={deployed_agent.status}")


# %% [markdown]
"""
## Context writes

``create_note`` and ``create_link``. ``create_saved_query`` needs a ``connection_id``
(not exposed in the SDK yet). Updates use ``context.items.update()``.
"""

# %%
print("=== Context items (first page) ===")
page = read.context.items.list(page_size=10)
for item in page:
    label = item.title or item.description or "(no title)"
    marker = "  <- example" if (item.title or "").startswith(EXAMPLE_PREFIX) else ""
    print(f"  [{item.context_type}] {label}  uid={item.uid[:8]}…{marker}")

if not RUN_WRITES:
    print("\nRead-only — set RUN_WRITES = True to create sample context items.")
else:
    created_uids: list[str] = []

    note_title = f"{EXAMPLE_PREFIX} Fiscal Year {_stamp()}"
    note_content = (
        "# Fiscal Year\n\nOur fiscal year runs **February 1 – January 31**.\n\n"
        "_Created by modus_management_guide.py. Safe to delete._"
    )
    print(f"\n=== Creating note: {note_title!r} ===")
    try:
        note = mgmt.context.create_note(title=note_title, content=note_content)
        created_uids.append(note.context_item_id)
        created["note_uid"] = note.context_item_id
        print(f"  uid={note.context_item_id}")
    except modus.InternalServerError as exc:
        print(f"  Skipped note — {exc}")

    link_title = f"{EXAMPLE_PREFIX} Python json docs {_stamp()}"
    print("\n=== Creating link ===")
    try:
        link = mgmt.context.create_link(
            url="https://docs.python.org/3/library/json.html",
            title=link_title,
            is_crawl=False,
        )
        created_uids.append(link.context_item_id)
        print(f"  uid={link.context_item_id}")
    except modus.ModusError as exc:
        print(f"  Skipped link — {exc.status_code}: {exc.message}")

    if created_uids:
        note_uid = created.get("note_uid")
        if note_uid:
            print("\n=== Updating note ===")
            updated_item = mgmt.context.items.update(
                str(note_uid),
                description="Updated by the management guide.",
            )
            print(f"  description={updated_item.description!r}")

    created["context_uids"] = created_uids


# %% [markdown]
"""
## Skill memories (read-only)

``mgmt.skills.memories(skill_id).list()`` and ``.search()``.
"""

# %%
if not skills:
    print("No skills — skip memories demo.")
else:
    skill_id = skills[0].id
    memories = mgmt.skills.memories(skill_id)
    mem_page = memories.list(page_size=10)
    print(f"=== Memories for skill id={skill_id} ===")
    print(f"  listed={len(mem_page)}")
    for idx, mem in enumerate(mem_page.items[:5], 1):
        preview = (mem.memory or "").replace("\n", " ")[:80]
        if len(mem.memory or "") > 80:
            preview += "…"
        print(f"  {idx}. [{mem.id}] {preview or '(empty)'}")

    if mem_page.items:
        result = memories.search(MemorySearchRequest(query="preferences", limit=5))
        print(f"\n  search matches={len(result.memories)}")


# %% [markdown]
"""
## Cleanup (optional)

Deletes only resources created in this run when ``CLEANUP = True``.
"""

# %%
if RUN_WRITES and CLEANUP:
    print("=== Cleanup ===")
    if "skill_id" in created:
        mgmt.skills.delete(created["skill_id"])
        print(f"  deleted skill id={created['skill_id']}")
    if "agent_id" in created:
        mgmt.agents.delete(created["agent_id"])
        print(f"  deleted agent id={created['agent_id']}")
    for uid in created.get("context_uids", []):
        deletion = mgmt.context.items.delete(uid)
        print(f"  deleted context uid={deletion.uid}")
elif RUN_WRITES:
    print("Resources left in place (CLEANUP=False). Created IDs:")
    for key, value in created.items():
        print(f"  {key}={value}")
else:
    print("No cleanup needed (read-only run).")


# %% [markdown]
"""
## Error handling

Management errors use the same ``modus.*`` hierarchy as the consumption client.
This demo clears ``MODUS_API_KEY`` briefly to trigger ``AuthenticationError``.
"""

# %%
print("=== Error handling patterns ===")
print("  AuthenticationError     — invalid or missing PAT")
print("  PermissionDeniedError   — missing skills:write / agents:write / context:write")
print("  UnprocessableError      — validation failed; inspect e.errors")
print("  InternalServerError     — e.g. S3 not wired in local stacks")

_saved_api_key = os.environ.pop("MODUS_API_KEY", None)
try:
    modus.Modus()
except modus.AuthenticationError:
    print("\nOK — caught AuthenticationError (demo)")
finally:
    if _saved_api_key is not None:
        os.environ["MODUS_API_KEY"] = _saved_api_key
