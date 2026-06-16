<p align="center">
  <img
    src="https://raw.githubusercontent.com/modus-data/modus-sdk-python/main/assets/modus-logo.png"
    alt="Modus"
    width="280"
  />
</p>

# Modus Python SDK

[![TestPyPI](https://img.shields.io/badge/TestPyPI-modus--sdk-blue)](https://test.pypi.org/project/modus-sdk/)
[![Python versions](https://img.shields.io/badge/python-3.10%2B-blue)](https://test.pypi.org/project/modus-sdk/)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)

Official Python client for Modus — your organization's context layer for AI.

## What is Modus?

Modus is your organization's context layer: it connects assistants to curated knowledge about your data, systems, and workflows so answers use org-specific context instead of generic guesses.

- **Modus** — your org-wide assistant (same capability as the Modus home page)
- **Skills** — published assistants you chat with, each with its own context and tools
- **Agents** — automations that run on a schedule or trigger
- **Context items** — curated knowledge Modus composes at runtime when answering

## Two clients in one package

**`modus.Modus()`** is what most people need. Use it to chat with Modus, run skills, browse context, and inspect agent runs — the same things you do in the Modus app day to day.

**`modus.management.ModusManagement()`** is for org setup: create, update, and deploy skills, agents, and context — the CRUD operations you would use in the Modus UI as an admin.

If you are getting started, use `Modus()` only. Reach for `ModusManagement()` when you are automating configuration.

Async variants: `AsyncModus` and `AsyncModusManagement`.

## Installation

Pre-release on [TestPyPI](https://test.pypi.org/project/modus-sdk/) (production PyPI coming later):

```bash
pip install -i https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ modus-sdk
```

## Getting started

```python
import modus

# Reads MODUS_API_KEY env var, or pass api_key= explicitly
client = modus.Modus()

for skill in client.skills.list():
    print(skill.name, skill.status)

skill = client.skills.get("revenue-analysis")
print(skill.name, skill.description)

for item in client.context.items.list():
    print(item.uid, item.context_type, modus.context_item_label(item))
```

## Authentication

Create an API token in the Modus app (**Settings → API Tokens** on your Modus home page). Prefer an environment variable over hardcoding keys in source:

```bash
export MODUS_API_KEY=modus_xxx
```

```python
client = modus.Modus(api_key="modus_xxx")
```

## Using Modus

### Modus vs skills

| Surface | SDK | Use when |
|---------|-----|----------|
| **Modus** (org-wide) | `client.modus.*` | Full-environment assistant — same as the Modus home page |
| **Skill** | `client.skills.*` | A specific published skill and its configured context/tools |

Use `client.modus.chat()` for native Modus — not `skills.chat(0)` or any other skill id shortcut.

### Org-wide Modus assistant

```python
MODEL = "claude-sonnet-4.6"

result = client.modus.chat("What were our top revenue drivers last quarter?", model=MODEL)
print(result.content, result.thread_id)

follow_up = client.modus.chat(
    "Break that down by region.",
    model=MODEL,
    thread_id=result.thread_id,
)
print(follow_up.content)

with client.modus.chat_stream("Summarize this week", model=MODEL) as stream:
    for chunk in stream.text_stream:
        print(chunk, end="")

ctx = client.modus.get_context("What tables describe customer churn?", limit=10)
print(ctx.original_count, ctx.session_id)

for row in client.modus.conversations.list(kind="modus", page_size=10):
    print(row.thread_id, row.first_message)
```

### Skills

```python
MODEL = "claude-sonnet-4.6"

result = client.skills.chat(skill_id, "Hello", model=MODEL)
print(result.content, result.thread_id)

with client.skills.chat_stream(skill_id, "Hi", model=MODEL) as stream:
    for chunk in stream.text_stream:
        print(chunk, end="")
```

### Context

```python
for item in client.context.items.list():
    print(item.uid, modus.context_item_label(item))
```

### Agents

```python
agent = client.agents.get(agent_id)
for run in client.agents.runs.list(agent_id, page_size=20):
    print(run.id, run.status)
```

Agent chat is not on the public PAT surface. Use `client.modus.chat()` for org-wide conversation or `client.skills.chat()` for a published skill.

## Managing your org

```python
from modus.management import ModusManagement

mgmt = ModusManagement()  # reads MODUS_API_KEY
skill = mgmt.skills.create(name="Analyst", model="gpt-4o")
mgmt.skills.deploy(skill.id)
```

Requires a token with write access to skills and agents (same as the Modus UI).

## Pagination

List endpoints return a `Page[T]`. Iterate the current page, or use `.auto_paging_iter()` for all pages:

```python
for skill in client.skills.list().auto_paging_iter():
    print(skill.name)
```

`client.modus.conversations.list()` accepts `kind="modus"`, `"skills"`, or `"all"` (default).

## Async

```python
import asyncio
import modus

async def main():
    async with modus.AsyncModus() as client:
        result = await client.modus.chat("Hello", model="claude-sonnet-4.6")
        print(result.content)

        async for skill in client.skills.list().auto_paging_iter():
            print(skill.name)

asyncio.run(main())
```

## Error handling

```python
try:
    skill = client.skills.get(999)
except modus.NotFoundError:
    print("Skill not found")
except modus.AuthenticationError:
    print("Check your MODUS_API_KEY")
except modus.RateLimitError as e:
    print(f"Rate limited. Retry after {e.retry_after}s")
except modus.ModusError as e:
    print(f"API error {e.status_code}: {e.message}")
```

## Examples

Runnable scripts ship with the package:

- `examples/scripts/quickstart.py` — list skills and context (`Modus`)
- `examples/scripts/modus_chat.py` — buffered and streaming Modus chat, context compose, conversations
- `examples/scripts/chat.py` — buffered skill chat with thread follow-up
- `examples/scripts/manage_skill.py` — create and deploy a skill (`ModusManagement`, `--write` optional)

Optional Streamlit demo: `examples/apps/modus_skill_chat/` (streaming vs buffered skill chat side by side).
