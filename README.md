<p align="center">
  <img
    src="https://raw.githubusercontent.com/modus-data/modus-sdk-python/main/assets/modus-logo.png"
    alt="Modus"
    width="280"
  />
</p>

# Modus Python SDK

[![PyPI](https://img.shields.io/pypi/v/modus-sdk)](https://pypi.org/project/modus-sdk/)
[![Python versions](https://img.shields.io/pypi/pyversions/modus-sdk)](https://pypi.org/project/modus-sdk/)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)

Official Python client for Modus — your organization's context layer for AI.

## What is Modus?

Modus is your organization's context layer: it connects assistants to curated knowledge about your data, systems, and workflows so answers use org-specific context instead of generic guesses.

- **Modus** — your org-wide assistant (same capability as the Modus home page)
- **Scopes** — published assistants you chat with, each with its own context and tools
- **Workflows** — automations that run on a schedule or trigger
- **Context items** — curated knowledge Modus composes at runtime when answering

## Two clients in one package

**`modus.Modus()`** is what most people need. Use it to chat with Modus, run scopes, browse context, upload ingested data, and inspect workflow runs — the same things you do in the Modus app day to day.

**`modus.management.ModusManagement()`** is for org setup: create, update, and deploy scopes, workflows, and context — the CRUD operations you would use in the Modus UI as an admin.

If you are getting started, use `Modus()` only. Reach for `ModusManagement()` when you are automating configuration.

Async variants: `AsyncModus` and `AsyncModusManagement`.

## Installation

```bash
pip install modus-sdk
```

Requires Python 3.10+.

## Getting started

```python
import modus

# Reads MODUS_API_KEY env var, or pass api_key= explicitly
client = modus.Modus()

for scope in client.scopes.list():
    print(scope.name, scope.status)

scope = client.scopes.get("revenue-analysis")
print(scope.name, scope.description)

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

### Modus vs scopes

| Surface | SDK | Use when |
|---------|-----|----------|
| **Modus** (org-wide) | `client.modus.*` | Full-environment assistant — same as the Modus home page |
| **Scope** | `client.scopes.*` | A specific published scope and its configured context/tools |

Use `client.modus.chat()` for native Modus — not `scopes.chat(0)` or any other scope id shortcut.

### Org-wide Modus assistant

```python
MODEL = "claude-sonnet-5"

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

### Scopes

```python
MODEL = "claude-sonnet-5"

result = client.scopes.chat(scope_id, "Hello", model=MODEL)
print(result.content, result.thread_id)

with client.scopes.chat_stream(scope_id, "Hi", model=MODEL) as stream:
    for chunk in stream.text_stream:
        print(chunk, end="")
```

### Context

```python
for item in client.context.items.list():
    print(item.uid, modus.context_item_label(item))
```

### Ingested data

Upload the exact SQL request and CSV response through the regular `Modus` client. With
`MODUS_API_KEY` configured as above, set `MODUS_ORGANIZATION_ID` to the organization
associated with the token:

```python
import os

import modus

client = modus.Modus()  # reads MODUS_API_KEY
stored = client.ingested_data.upload(
    organization_id=os.environ["MODUS_ORGANIZATION_ID"],
    integration_type="postgresql",
    request={"type": "sql", "query": "SELECT id, name FROM customers"},
    response={"format": "csv", "content": "id,name\n1,Ada\n"},
)
print(stored.checksum, stored.key)
```

The token must include the `context:write` permission.

### Workflows

```python
workflow = client.workflows.get(workflow_id)
for run in client.workflows.runs.list(workflow_id, page_size=20):
    print(run.id, run.status)
```

Workflow chat is not on the public PAT surface. Use `client.modus.chat()` for org-wide conversation or `client.scopes.chat()` for a published scope.

## Managing your org

```python
from modus.management import ModusManagement

mgmt = ModusManagement()  # reads MODUS_API_KEY
scope = mgmt.scopes.create(name="Analyst", model="claude-sonnet-5")
mgmt.scopes.deploy(scope.id)

# Create returns context_item_id (also available as .uid); list/get use .uid
note = mgmt.context.create_note("Title", "Body")
print(note.context_item_id, note.uid)  # same UUID

upload = mgmt.context.files.upload("report.pdf")
print(upload.upload_id, upload.status)

result = mgmt.context.files.upload_dir("./reports")
print(len(result.uploaded), len(result.failed))
```

Requires a token with write access to scopes and workflows (same as the Modus UI).

## Pagination

List endpoints return a `Page[T]`. Iterate the current page, or use `.auto_paging_iter()` for all pages:

```python
for scope in client.scopes.list().auto_paging_iter():
    print(scope.name)
```

`client.modus.conversations.list()` accepts `kind="modus"`, `"skills"`, or `"all"` (default).

## Async

```python
import asyncio
import modus

async def main():
    async with modus.AsyncModus() as client:
        result = await client.modus.chat("Hello", model="claude-sonnet-5")
        print(result.content)

        async for scope in client.scopes.list().auto_paging_iter():
            print(scope.name)

asyncio.run(main())
```

## Error handling

```python
try:
    scope = client.scopes.get(999)
except modus.NotFoundError:
    print("Scope not found")
except modus.AuthenticationError:
    print("Check your MODUS_API_KEY")
except modus.RateLimitError as e:
    print(f"Rate limited. Retry after {e.retry_after}s")
except modus.ModusError as e:
    print(f"API error {e.status_code}: {e.message}")
```

## Examples

Runnable scripts ship with the package:

- `examples/scripts/quickstart.py` — list scopes and context (`Modus`)
- `examples/scripts/modus_chat.py` — buffered and streaming Modus chat, context compose, conversations
- `examples/scripts/chat.py` — buffered scope chat with thread follow-up
- `examples/scripts/manage_skill.py` — create and deploy a scope (`ModusManagement`, `--write` optional)

Optional Streamlit demo: `examples/apps/modus_skill_chat/` (streaming vs buffered scope chat side by side).

## Docs

Full guides: [docs.getmodus.com/guides/sdk](https://docs.getmodus.com/guides/sdk) (Python page: [sdk-python](https://docs.getmodus.com/guides/sdk-python)).
