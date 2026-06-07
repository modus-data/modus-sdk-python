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

- **Skills** — interactive assistants you chat with
- **Agents** — automations that run on a schedule or trigger
- **Context items** — curated knowledge Modus composes at runtime when a skill or agent answers

## Two clients in one package

**`modus.Modus()`** is what most people need. Use it to run skills, chat, browse context, and trigger agents — the same things you do in the Modus app day to day.

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
    print(item.uid, item.type, item.title)
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

### Skills

```python
MODEL = "claude-sonnet-4.6"

result = client.skills.chat(skill_id, "Hello", model=MODEL)
print(result.text, result.thread_id)

with client.skills.chat_stream(skill_id, "Hi", model=MODEL) as stream:
    for chunk in stream.text_stream:
        print(chunk, end="")
```

### Context

```python
for item in client.context.items.list():
    print(item.uid, item.title)
```

### Agents

```python
client.agents.chat(agent_id, "Run report", model=MODEL)
for run in client.agents.runs.list(agent_id, page_size=20):
    print(run.id, run.status)
```

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

## Async

```python
import asyncio
import modus

async def main():
    async with modus.AsyncModus() as client:
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
- `examples/scripts/chat.py` — buffered and streaming skill chat
- `examples/scripts/manage_skill.py` — create and deploy a skill (`ModusManagement`, `--write` optional)

Optional Streamlit demo: `examples/apps/modus_skill_chat/` (streaming vs buffered side by side).
