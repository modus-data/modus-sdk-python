<p align="center">
  <a href="https://modus.com">
    <img
      src="https://raw.githubusercontent.com/modus-data/modus-sdk-python/main/assets/modus-logo.png"
      alt="Modus"
      width="280"
    />
  </a>
</p>

# Modus Python SDK

[![TestPyPI](https://img.shields.io/badge/TestPyPI-modus--sdk-blue)](https://test.pypi.org/project/modus-sdk/)
[![Python versions](https://img.shields.io/badge/python-3.10%2B-blue)](https://test.pypi.org/project/modus-sdk/)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)

Official Python client for the [Modus](https://modus.com) AI data platform.

## Installation

Published on [TestPyPI](https://test.pypi.org/project/modus-sdk/) (production PyPI coming later):

```bash
pip install -i https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ modus-sdk
```

## Quick Start

```python
import modus

# Reads MODUS_API_KEY env var, or pass api_key= explicitly
client = modus.Modus()

# List skills
for skill in client.skills.list():
    print(skill.name, skill.status)

# Get a skill by slug or id
skill = client.skills.get("revenue-analysis")
print(skill.name, skill.description)

# List context items (your knowledge base)
for item in client.context.items.list():
    print(item.uid, item.type, item.title)
```

## Authentication

Create a token at **app.modus.com → Settings → API Tokens**.

```bash
export MODUS_API_KEY=modus_xxx
```

Or pass it directly:

```python
client = modus.Modus(api_key="modus_xxx")
```

## Configuration

| Variable | Required | Description |
|----------|----------|-------------|
| `MODUS_API_KEY` | Yes | Personal access token (`modus_…`) |

By default the client uses `https://api.modus.com`. For staging or other hosted
environments, pass `base_url` when constructing the client. The token must be
issued for the same environment.

```python
client = modus.Modus(
    api_key="modus_xxx",
    base_url="https://api.staging.getmodus.com",
)
```

Optional constructor arguments: `timeout` (default 5s connect, 300s read) and
`max_retries` (default `2` on 429/5xx).

## API reference

Interactive OpenAPI docs for the public REST API:

- [Swagger UI](https://api.modus.com/api/v1/docs)
- [OpenAPI JSON](https://api.modus.com/api/v1/docs-json)

## Pagination

List endpoints return a `Page[T]`. Iterating gives the current page.
Use `.auto_paging_iter()` to iterate across all pages.

```python
# Current page only (default 25 items)
page = client.skills.list(page_size=25)
for skill in page:
    print(skill.name)

# All pages (uses page.next_page_token between requests)
for skill in client.skills.list().auto_paging_iter():
    print(skill.name)

# Manual control
if page.has_next_page():
    next_page = page.get_next_page()
```

## Async

```python
import asyncio
import modus

async def main():
    async with modus.AsyncModus() as client:
        page = await client.skills.list()
        for skill in page:
            print(skill.name)

asyncio.run(main())
```

## Error Handling

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

## Managing skills, agents & context

The same package ships a management client for configuration (requires a
PAT with `skills:write` / `agents:write`):

```python
from modus.management import ModusManagement

mgmt = ModusManagement()  # reads MODUS_API_KEY
skill = mgmt.skills.create(name="Analyst", model="gpt-4o")
mgmt.skills.deploy(skill.id)
```

Errors are the shared `modus.*` hierarchy (`modus.NotFoundError`, etc.).

## Chat

```python
MODEL = "claude-sonnet-4.6"

result = client.skills.chat(skill_id, "Hello", model=MODEL)
print(result.text, result.thread_id)

with client.skills.chat_stream(skill_id, "Hi", model=MODEL) as stream:
    for chunk in stream.text_stream:
        print(chunk, end="")
    final = stream.get_final_result()

ctx = client.skills.get_context(skill_id, "What tables describe revenue?", limit=25)
client.agents.chat(agent_id, "Run report", model=MODEL)
client.agents.runs.list(agent_id, page_size=20)
```

## Release notes

See [CHANGELOG.md](CHANGELOG.md) for version history.

## Capabilities

| Feature | Client |
|---|---|
| `client.skills.list/get`, `conversations`, `chat`, `chat_stream`, `get_context` | `Modus` |
| `client.agents.list/get`, `chat`, `chat_stream`, `runs.list/get` | `Modus` |
| `client.context.items.list/get/lookup/list_values` | `Modus` |
| `AsyncModus` | `Modus` |
| `mgmt.skills/agents/context` write APIs, `mgmt.skills.memories(...)` | `ModusManagement` |
| `AsyncModusManagement` | `ModusManagement` |

`ModusManagement` requires a PAT with `skills:write` / `agents:write` scopes.
