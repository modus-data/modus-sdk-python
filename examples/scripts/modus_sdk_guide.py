# %% [markdown]
"""
# Modus SDK Guide — Consumption Client

Read and invoke your Modus org with ``modus.Modus()`` (modus-sdk 0.1.3+).

Covers: skills, agents, context, conversations, chat/streaming, context compose,
agent runs, pagination, and error handling.

**Setup:** export ``MODUS_API_KEY`` in your shell (Settings → API Tokens in the Modus app).
"""

# %%
import os
from importlib.metadata import version

import modus

MODEL = "claude-sonnet-4.6"
RUN_CHAT = True  # set True to run LLM chat cells (uses API credits)
RUN_CONTEXT = False  # set True to also call get_context (404 on some environments)

print(f"modus-sdk {version('modus-sdk')}")
print(f"MODUS_API_KEY set: {bool(os.environ.get('MODUS_API_KEY'))}")

if not os.environ.get("MODUS_API_KEY"):
    raise SystemExit(
        "Export MODUS_API_KEY before running this guide:\n"
        "  export MODUS_API_KEY=modus_xxx"
    )

client = modus.Modus()
print("Connected with modus.Modus() — consumption / read + invoke client")


# %%
def _truncate(text: str, max_len: int = 80) -> str:
    if len(text) <= max_len:
        return text
    return text[: max_len - 1] + "…"


def _first_active_skill():
    for skill in client.skills.list().auto_paging_iter():
        if skill.is_active:
            return skill
    skills = list(client.skills.list().auto_paging_iter())
    return skills[0] if skills else None


def _first_agent():
    agents = list(client.agents.list().auto_paging_iter())
    return agents[0] if agents else None


# %% [markdown]
"""
## Org snapshot

List skills (active vs draft), agents, and a context summary.
Uses ``auto_paging_iter()`` to walk all pages.
"""

# %%
print("=== Skills ===")
active, draft = [], []
for skill in client.skills.list().auto_paging_iter():
    (active if skill.is_active else draft).append(skill)

print(f"  Active ({len(active)}):")
for skill in active:
    print(f"    • {skill.name}  (id={skill.id}, slug={skill.slug})")

print(f"  Draft ({len(draft)}):")
for skill in draft:
    flag = " [unpublished changes]" if skill.has_unpublished_changes else ""
    print(f"    • {skill.name}{flag}  (id={skill.id})")

print("\n=== Agents ===")
agents = list(client.agents.list().auto_paging_iter())
if not agents:
    print("  No agents found.")
else:
    for agent in agents:
        status = "active" if agent.is_active else "draft"
        print(f"  [{status}] {agent.name}  (type={agent.type}, id={agent.id})")

print("\n=== Context (summary) ===")
counts: dict[str, int] = {}
samples: list[tuple[str, str]] = []
for item in client.context.items.list().auto_paging_iter():
    counts[item.context_type] = counts.get(item.context_type, 0) + 1
    if len(samples) < 5:
        label = item.title or item.description or "(no title)"
        samples.append((item.context_type, _truncate(label)))

if not counts:
    print("  No context items yet.")
else:
    for kind, n in sorted(counts.items()):
        print(f"    {kind}: {n}")
    print(f"    Total: {sum(counts.values())}")
    print("\n  Sample items:")
    for kind, label in samples:
        print(f"    [{kind}] {label}")


# %% [markdown]
"""
## Pagination (AIP-158)

List endpoints use ``page_size`` (default 25) and ``page_token``.
``Page`` objects expose ``has_next_page()``, ``get_next_page()``, and
``auto_paging_iter()``.
"""

# %%
page = client.skills.list(page_size=5)
print(f"First page: {len(page)} skill(s), has_next={page.has_next_page()}")
for skill in page:
    print(f"  {skill.name} ({skill.status})")

if page.has_next_page():
    page2 = page.get_next_page()
    print(f"\nSecond page: {len(page2)} skill(s)")


# %% [markdown]
"""
## Skills — get and conversations

``skills.get()`` accepts a numeric skill id.
``skills.conversations`` lists and retrieves chat threads for a skill.
"""

# %%
skill = _first_active_skill()
if not skill:
    print("No skills — create one in the Modus app first.")
else:
    detail = client.skills.get(skill.id)
    print(f"Skill: {detail.name}")
    print(f"  id={detail.id}  status={detail.status}  slug={detail.slug}")

    conv_page = client.skills.conversations.list(skill.id, page_size=5)
    print(f"\nRecent conversations: {len(conv_page)} on this page")
    for conv in conv_page:
        preview = conv.first_message or ""
        if len(preview) > 60:
            preview = preview[:59] + "…"
        print(f"  thread {conv.thread_id[:8]}…  ({conv.message_count} msgs)  {preview!r}")

    if conv_page.items:
        thread = client.skills.conversations.get(skill.id, conv_page.items[0].thread_id)
        print(f"\nThread detail: {len(thread.messages)} message(s)")


# %% [markdown]
"""
## Context — list, get, lookup, list_values

Filter by type with ``context_type=``. ``lookup()`` returns ``None`` on no match.
``list_values()`` paginates array fields inside item content (best-effort).
"""

# %%
notes_page = client.context.items.list(page_size=5, context_type="note")
print(f"Notes on first page: {len(notes_page)}")

sample_page = client.context.items.list(page_size=1)
if not sample_page.items:
    print("No context items in org.")
else:
    item = sample_page.items[0]
    label = item.title or item.description or item.uid[:8]
    print(f"\nSample: [{item.context_type}] {label}")

    detail = client.context.items.get(item.uid)
    print("\ncontext.items.get:")
    print(f"  uid={detail.uid}  type={detail.context_type}  title={detail.title!r}")

    found = client.context.items.lookup(item.context_type, ["sdk", "example", "probe"])
    print("\ncontext.items.lookup:")
    print(f"  match={found.uid[:8] + '…' if found else None}")

    print("\ncontext.items.list_values (best-effort):")
    try:
        values_page = client.context.items.list_values(
            item.uid,
            item.context_type,
            "enumValues",
            page_size=5,
        )
        print(f"  rows={len(values_page)}  has_next={values_page.has_next_page()}")
        for idx, row in enumerate(values_page.items[:3], 1):
            print(f"    {idx}. {row}")
    except modus.ModusError as exc:
        print(f"  skipped ({exc.status_code}): {exc.message}")


# %% [markdown]
"""
## Skill chat and context compose

Set ``RUN_CHAT = True`` in the setup cell to run these (uses LLM credits).

- ``skills.chat()`` — buffered JSON reply
- ``skills.chat_stream()`` — SSE token stream; pass ``thread_id`` to continue
- ``skills.get_context()`` — preview RAG context without calling the LLM (optional;
  set ``RUN_CONTEXT = False`` to skip — some environments return 404 while chat works)
"""

# %%
if not RUN_CHAT:
    print("Chat skipped — set RUN_CHAT = True in the setup cell to enable.")
elif not skill:
    print("No skill available for chat.")
else:
    result = client.skills.chat(skill.id, "Say hello in one sentence.", model=MODEL)
    print(f"Buffered: {result.text}")
    print(f"  thread_id={result.thread_id}  run_id={result.run_id}")

    print("\nStreaming: ", end="", flush=True)
    with client.skills.chat_stream(
        skill.id,
        "What did I just ask?",
        model=MODEL,
        thread_id=result.thread_id,
    ) as stream:
        for chunk in stream.text_stream:
            print(chunk, end="", flush=True)
        follow_up = stream.get_final_result()
    print(f"\n  thread_id={follow_up.thread_id}")

    if RUN_CONTEXT:
        print("\nContext compose (get_context):")
        try:
            ctx = client.skills.get_context(
                skill.id,
                "What context is relevant to revenue?",
                limit=10,
            )
            print(f"  {ctx.original_count} considered, {len(ctx.context_items)} selected")
            print(f"  session_id={ctx.session_id}")
        except modus.NotFoundError:
            print(
                "  Skipped — context compose returned NotFoundError for this skill.\n"
                "  Chat works; get_context needs the context composer on the API side.\n"
                "  Set RUN_CONTEXT = False to skip this step."
            )
        except modus.ModusError as exc:
            print(f"  Skipped ({exc.status_code}): {exc.message}")


# %% [markdown]
"""
## Agents and automation runs

``agents.runs.list()`` supports filters: ``status``, ``timeframe``, ``search``.
"""

# %%
agent = _first_agent()
if not agent:
    print("No agents — skip runs demo.")
else:
    detail = client.agents.get(agent.id)
    print(f"Agent: {detail.name}  type={detail.type}  status={detail.status}")

    runs_page = client.agents.runs.list(agent.id, page_size=10, status="completed")
    print(f"\nCompleted runs (this page): {len(runs_page)}")
    for run in runs_page:
        ended = run.ended_at.strftime("%Y-%m-%d %H:%M") if run.ended_at else "in progress"
        print(f"  [{run.status}] {run.id}  ended={ended}")

    if runs_page.items:
        run_detail = client.agents.runs.get(agent.id, runs_page.items[0].id)
        print(f"\nRun detail: workflow_id={run_detail.workflow_id}")
        if run_detail.history is not None:
            n = len(run_detail.history) if isinstance(run_detail.history, list) else "present"
            print(f"  history entries: {n}")


# %% [markdown]
"""
## Error handling

All errors inherit from ``modus.ModusError``. This cell temporarily clears
``MODUS_API_KEY`` so the SDK raises ``AuthenticationError`` at init (no
hardcoded credential in source).
"""

# %%
print("=== Error handling demo (expected failure) ===")
_saved_api_key = os.environ.pop("MODUS_API_KEY", None)
try:
    modus.Modus()
except modus.AuthenticationError:
    print("OK — AuthenticationError (missing API key)")
except modus.ModusError as e:
    print(f"Unexpected — ModusError {e.status_code}: {e.message}")
finally:
    if _saved_api_key is not None:
        os.environ["MODUS_API_KEY"] = _saved_api_key

# %%
