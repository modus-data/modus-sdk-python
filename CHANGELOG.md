# Changelog

**Current release:** [`0.3.0`](https://pypi.org/project/modus-sdk/0.3.0/).



## [0.3.0] — 2026-07-26

> Breaking surface vs `0.2.x` (pre-1.0 minor bump). See `distribution/docs/COMPATIBILITY.md`.

### Added

- `mgmt.usage.list()` / `list_async()` gain an optional `user_email` filter (repeated query param).
- `mgmt.usage.list_users(since, until)` (sync + async) — distinct acting-user emails observed in the window.

### Deprecated

- **`Skill` / `Agent` type names** — use `Scope` / `Workflow` (and `ScopeStatus` / `WorkflowStatus`, `WorkflowType`, etc.). `Skill` and `Agent` remain as aliases.
- **`conversation_skill_id()`** — use `conversation_scope_id()`.

### Changed

- SDK read types are now exported as `Scope` / `Workflow` backed by generated `ScopeDto` / `WorkflowDto`.
- Custom context create responses always expose `.uid` (same value as `contextItemId`).

### Removed

- Dual list/deploy envelopes — responses use `scopes` / `workflows` and `scope` / `workflow` only (no `skills` / `agents` / `skill` / `agent` aliases).
- Public Python type aliases **`SkillDto` / `AgentDto`** — use `ScopeDto` / `WorkflowDto` (thin `Skill` / `Agent` aliases remain).
- Conversation `kind=skills` — use `kind=scopes` (`all` | `modus` | `scopes`).
- `ModusManagement.organization.delete()` — organization deletion is no longer
  part of the public API / PAT surface (SPA-only).
- `GET /api/v1/users/member-groups` and `/org-members` no longer advertise `pageSize` /
  `pageToken` query params or an always-`None` `next_page_token` response field (OpenAPI /
  Management MCP surface — `ModusManagement.users.list_member_groups()` /
  `list_org_members()` never exposed either). Both endpoints return the full org-bounded
  roster; pagination was never honored server-side.

### Fixed

- `examples/apps/modus_skill_chat/app.py` called the removed `client.skills` accessor
  (raised `AttributeError`); switched to `client.scopes.chat()` / `chat_stream()`.

## [Unreleased]

## [0.2.3] — 2026-07-20

### Fixed

- Streaming requests send `Accept: text/event-stream`; a non-SSE response (e.g. JSON polling body) raises `ModusError` instead of being silently treated as an empty stream.
- `runs.create()` / `create_modus()` / `create_scope()` / `resume()` always mint (or reuse) a `sessionId`, matching `chat_stream`'s existing behavior.

## [0.2.2] — 2026-07-20

### Fixed

- Streaming always sends `sessionId` (thread id or generated UUID) on agent-host runs.
- Optional `organization_id` / `MODUS_ORGANIZATION_ID` for stream bodies; agent-service accepts omitted org and uses the PAT principal.
- Default API/agent hosts are `*.getmodus.com` (no longer `*.modus.com`).
- `base_urls['agent-service']` drives the streaming agent-host client (parity with TypeScript).

### Added

- Create responses expose `.uid` as an alias of `context_item_id`.

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

- Legacy **`client.skills` / `client.agents`** accessors (and management equivalents).
