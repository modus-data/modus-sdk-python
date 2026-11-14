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

# list() returns one page; auto_paging_iter() follows every page
for scope in client.scopes.list().auto_paging_iter():
    print(scope.name, scope.status)

# Ids are numeric: take one from list()
first = client.scopes.list().items[0]
scope = client.scopes.get(first.id)
print(scope.name, scope.description)

for item in client.context.items.list().auto_paging_iter():
    print(item.uid, item.context_type, modus.context_item_label(item))
```

## Authentication

Create an API token in the Modus app (**Settings → API Tokens** on your Modus home page). Prefer an environment variable over hardcoding keys in source:

```bash
export MODUS_API_KEY=modus_pat_xxx
```

```python
client = modus.Modus(api_key="modus_pat_xxx")
```

### Staging and custom hosts

The client talks to `https://api.getmodus.com` by default. Chat and runs go to the agent host,
which for a Modus API origin is derived from it (`api.staging.getmodus.com` →
`agent.staging.getmodus.com`). Point the client elsewhere with arguments or environment variables:

| Argument | Environment variable | Default |
|----------|----------------------|---------|
| `base_url` | `MODUS_BASE_URL` | `https://api.getmodus.com` |
| `agent_host` | `MODUS_AGENT_HOST` | derived from `base_url`: `api.getmodus.com` → `agent.getmodus.com`, `api.<env>.getmodus.com` → `agent.<env>.getmodus.com`; none for any other host |

```python
staging = modus.Modus(base_url="https://api.staging.getmodus.com")

# A host that is not api.getmodus.com or api.<env>.getmodus.com needs its agent host too, or chat and runs raise
self_hosted = modus.Modus(
    base_url="https://modus-api.internal.example.com",
    agent_host="https://modus-agent.internal.example.com",
)
```

An argument wins over its environment variable. `ModusManagement` and the async clients take the
same arguments.

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

result = client.modus.chat("What were our top revenue drivers last quarter?", model=MODEL).result()
print(result.content, result.thread_id)

# Every chat streams live from the agent host; iterate it to print tokens as they arrive.
with client.modus.chat("Break that down by region.", model=MODEL, thread_id=result.thread_id) as chat:
    for chunk in chat.text_stream:
        print(chunk, end="")

ctx = client.modus.get_context("What tables describe customer churn?", limit=10)
print(ctx.original_count, ctx.session_id)

for row in client.modus.conversations.list(kind="modus", page_size=10):
    print(row.thread_id, row.first_message)
```

### Scopes

```python
MODEL = "claude-sonnet-5"

result = client.scopes.chat(scope_id, "Hello", model=MODEL).result()
print(result.content, result.thread_id)

with client.scopes.chat(scope_id, "Hi", model=MODEL, thread_id=result.thread_id) as chat:
    for chunk in chat.text_stream:
        print(chunk, end="")
```

### Approvals

A run that needs approval for a write stops with `result.approval` set. Continue it with `resume`:

```python
chat = client.modus.chat("Fix the typo in the accounts table", model=MODEL)
if chat.result().approval:
    print(chat.resume(decision="approve").result().content)
```

Async: `await client.modus.chat(...)` returns the result; `async with` / `async for` stream it.

### Context

```python
for item in client.context.items.list().auto_paging_iter():
    print(item.uid, modus.context_item_label(item))

# One read-only SQL statement over the items you can read (at most 1,000 rows; `truncated` says when cut).
# Off by default for an organization; ask Modus to enable it.
from modus.types.context import ContextItemsQuery

result = client.context.items.query(
    ContextItemsQuery(sql="SELECT context_type, count(*) AS items FROM context_items GROUP BY context_type ORDER BY items DESC")
)
print(result.rows, result.truncated)
```

### Connections

`list_selections` returns one page of the units a scope can select on a connection
(`ConnectionSelection`: `path`, `object_type`, `display_name`); `iter_selections` follows every page:

```python
connection = client.connections.find(name="GitHub")  # None when no connection has that name
if connection is not None:
    for unit in client.connections.iter_selections(connection.id):
        print(unit.object_type, unit.display_name, unit.path)
```

### Ingested data

Upload the exact SQL request and CSV response through the regular `Modus` client. The
organization comes from the configured `MODUS_API_KEY`:

```python
import modus

client = modus.Modus()  # reads MODUS_API_KEY
stored = client.ingested_data.upload(
    integration_type="postgresql",
    request={"type": "sql", "query": "SELECT id, name FROM customers"},
    response={"format": "csv", "content": "id,name\n1,Ada\n"},
)
print(stored.checksum)
```

The token must include the `context:write` permission.

### Workflows

```python
workflow = client.workflows.get(workflow_id)
for run in client.workflows.runs.list(workflow_id, page_size=20):
    print(run.id, run.status)

# Chat with a published workflow; result() returns its final output.
digest = client.workflows.chat(workflow_id, "Run this week's digest", model="claude-sonnet-5").result()
print(digest.content)
```

`client.workflows.runs.stream(run_id)` follows a run's events. Each event carries an `id` when the server sends one. If the connection drops, call `stream` again with `last_event_id` set to the last `id` you handled: the stream resumes after it instead of replaying the run from the start. Without an `id` it can only replay from the start. The stream ends after a `done`, `error` or `cancelled` event; only `done` is a completed run.

```python
from modus import APIConnectionError


def follow_run(run_id, handle):
    last_id = None
    while True:
        events = iter(client.workflows.runs.stream(run_id, last_event_id=last_id))
        while True:
            try:
                event = next(events)
            except StopIteration:
                break  # ended without a final event: resume
            except APIConnectionError:
                break  # dropped: resume after last_id
            handle(event)  # a handler error propagates; it is not a disconnect
            last_id = event.id or last_id
            if event.type == "done":
                return
            # A stream_timeout event is followed by an error event.
            if event.type in ("error", "cancelled"):
                raise RuntimeError(f"Run {run_id} ended with {event.type}")
```

## Managing your org

```python
from modus.management import ModusManagement

mgmt = ModusManagement()  # reads MODUS_API_KEY
scope = mgmt.scopes.create(name="Analyst", model="claude-sonnet-5")
mgmt.scopes.deploy(scope.id)

# Create returns context_item_id (also available as .uid); list/get use .uid
note = mgmt.context.create_note("Title", "Body")
related_note = mgmt.context.create_note("Related title", "Related body")
print(note.context_item_id, note.uid)  # same UUID

upload = mgmt.context.files.upload("report.pdf")
print(upload.upload_id, upload.status)

result = mgmt.context.files.upload_dir("./reports", folder_path="finance")
print(len(result.uploaded), len(result.failed))
file = mgmt.context.files.get(upload.upload_id)
files = mgmt.context.files.list()
print(file.status, len(files.items))

root_folders = mgmt.context.items.list(
    connection_ids=["files"],
    context_type="file_folder_metadata",
    parent_uids=[],
)
print(len(root_folders.items))

# Move the uploaded file into a root folder (destination_folder_uid=None moves it back to the root)
if root_folders.items:
    moved = mgmt.context.items.move(
        upload.upload_id,
        destination_folder_uid=root_folders.items[0].uid,
    )
    print(moved.moved_items)  # 1, or 0 when it was already there

# Who can view and manage a note, saved query, link or uploaded file; all three settings replace the current ones.
access = mgmt.context.items.update_access(
    note.uid,
    visibility="private",
    group_permissions={},
    # Replace with the email of a member of your organization; anyone else is a 422
    shared_with=[{"email": "ana@example.com", "permission": "use"}],
)
print(access.can_manage)

upserted = mgmt.context.custom_items.create_relations([
    {
        "from_uid": note.uid,
        "to_uid": related_note.uid,
        "relation_type": "depends_on",
    }
])
print(upserted)
```

Requires a token with write access to scopes, workflows, and context (same as the Modus UI). Custom context items and relations need the `context:write` permission, and custom
context item writes must be enabled for your organization. They are off by default: until Modus
enables them, `custom_items` writes raise `PermissionDeniedError` ("Custom context item writes are
not enabled"). Ask Modus to turn them on.

### Toolsets

Choose each integration's Modus connection UUID explicitly. Grants and optional rules apply
only to that connection; a runner without access to it cannot use its tools.

```python
from modus.management import Toolset

# Use connection ids from client.connections.list().
toolset = Toolset.combine(
    Toolset.slack(connection_id=slack_connection_id, actions=["SendMessage"]),
    Toolset.sql("snowflake", connection_id=sql_connection_id),
    Toolset.memory(),
)
mgmt.scopes.update(scope.id, toolset=toolset)
```

`Toolset.integration(name, connection_id=..., actions=..., rules=...)` supports all
integration platform keys. Action names have no connection/path suffixes. SQL grants
`query`; scope selections control which data it can query. `combine` and `merge`
replace an earlier entry for the same platform with the later entry.

`scopes.update` replaces whole lists such as `connection_set`, `context_selections`, and `evaluations`. Add or change one evaluation case with `scopes.evaluations(id).add_case`, `update_case`, or `delete_case`. Change one connection's selection with `apply_selection_ops` (`validate_only=True` previews and does not write). Each `connectionSet` entry is `{ connection_id, preferences }`; remove a connection with the `removeConnection` op.

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

        async for scope in (await client.scopes.list()).auto_paging_iter():
            print(scope.name)

asyncio.run(main())
```

## Error handling

```python
try:
    scope = client.scopes.get(999)
except modus.NotFoundError:
    print("Scope not found")
except modus.BadRequestError as e:
    print(f"Invalid request: {e.message}")
except modus.AuthenticationError:
    print("Check your MODUS_API_KEY")
except modus.PermissionDeniedError as e:
    print("Token is missing scopes:", (e.info or {}).get("missing"))
except modus.RateLimitError as e:
    print(f"Rate limited. Retry after {e.retry_after}s")
except modus.ValidationError as e:
    # Rejected by the SDK before any request was sent, so there is no status or request_id
    print(f"Invalid argument: {e.message}")
except modus.ModusError as e:
    print(f"API error {e.status_code} {e.code}: {e.message} (request {e.request_id}, trace {e.trace_id})")
```

Every error the server returns carries `status_code`, `code` (for example `NOT_FOUND`) and
`trace_id`, plus `request_id` when the response supplies one (quote both to support), and, when
the server sends one, `info` with structured detail. An `APIConnectionError` (the request never got a response) carries only
`trace_id`, which names the call even though it never reached Modus. A `ValidationError` (for
example an unsupported chat model) is raised by the SDK before a request is sent, so it has none
of these. A request that fails schema
validation raises `BadRequestError` (400); one that is well-formed but breaks a business
rule raises `UnprocessableError` (422), with the rule in `info`.

## Retries

A failed request is re-sent up to `max_retries` times (default 2, with exponential
backoff), but only when sending it twice cannot do the work twice:

- **429**, for every method. A `Retry-After` (or `retry-after-ms`) of up to 60 s is waited
  out; a longer one raises `RateLimitError` at once with `retry_after` set.
- **A connection that never opened** (refused, DNS failure, connect or pool timeout), for
  every method.
- **408, 500, 502, 503, 504, a dropped connection or a timeout**, for GET, PUT, PATCH and
  DELETE, and for the POSTs that only read or set a state (context compose, item lookup,
  memory search, active-run lookup, run cancel, run interrupt, workflow-action cancel, workflow toggle,
  ingested-data upload).

Any other POST (a create, an add, an evaluation run) may already have run on the server,
so it raises instead of being re-sent: check whether the resource exists before creating
it again. `e.retryable` tells you whether the SDK considered the failure safe to re-send.
Pass `max_retries=0` to turn retries off.

## Examples

Runnable scripts live in the [GitHub repository](https://github.com/modus-data/modus-sdk-python/tree/main/examples/scripts),
not in the installed package. Clone it to run them:

- `examples/scripts/quickstart.py` — list scopes and context (`Modus`)
- `examples/scripts/modus_chat.py` — awaited and streamed Modus chat, context compose, conversations
- `examples/scripts/chat.py` — scope chat with thread follow-up
- `examples/scripts/manage_skill.py` — create and deploy a scope (`ModusManagement`, `--write` optional)


## Docs

Full guides: [docs.getmodus.com/guides/sdk](https://docs.getmodus.com/guides/sdk) (Python page: [sdk-python](https://docs.getmodus.com/guides/sdk-python)).
