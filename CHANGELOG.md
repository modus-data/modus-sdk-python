# Changelog

**Current release:** [`0.2.2`](https://pypi.org/project/modus-sdk/0.2.2/).


## [Unreleased]

## [0.2.2] — 2026-07-20

## [0.2.0] — 2026-07-20

### Added

- **`modus.Modus` / `AsyncModus`** — read and invoke: scopes, workflows, context, connections, Modus assistant chat, runs, suggestions.
- **`modus.management.ModusManagement` / `AsyncModusManagement`** — configure: CRUD, deploy, context creators, usage, org admin, scope evaluations.
- Canonical **`client.scopes` / `client.workflows`** (and management equivalents) against `/api/v1/scopes` and `/api/v1/workflows`.
- **`client.modus`** — org-wide Modus assistant (`chat`, `chat_stream`, `get_context`, `conversations`).
- **`client.suggestions`** — list approved suggested questions; record impression/click/dismiss events.
- **`client.workflows.runs.active()` / `active_by_session(...)`** — list or look up active conversation runs.
- **`mgmt.scopes.evaluations(scope_id)`** — evaluation config, manual trigger, run history.
- Bounded conversation windows via optional `message_limit` / `before_message_index` on `conversations(...).get()`.
- MCP **`get_context_data`** batch + ACL: `{ items: [{ itemId, field?, mode?, limit? }, …], sessionId? }` → `{ results: [...] }` (max 20; per-item partial failures).
- Cursor pagination, retries on 429/5xx, SSE streaming chat.
- Full public OpenAPI operation coverage (contract-tested).

### Changed

- Public surface uses **Scope** / **Workflow** vocabulary (types remain `Skill` / `Agent` where the API still uses those names).
- Scope-run helper: `client.workflows.runs.create_scope(scope_id, body)` (not `create_skill`).

### Removed

- Legacy **`client.skills` / `client.agents`** accessors — use `scopes` / `workflows`.
- Unimplemented context-creator stubs (`dimension` / `fact` / `metric` / `filter` create DTOs).

## Prior (TestPyPI only)

| Version | Notes |
|---------|--------|
| 0.1.0–0.1.7 | Internal / TestPyPI previews. Not published to production PyPI. Superseded by `0.2.0`. |
