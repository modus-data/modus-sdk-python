# Changelog

**Current release:** [`0.2.3`](https://pypi.org/project/modus-sdk/0.2.3/).



## [Unreleased]

### Deprecated

- **`Skill` / `Agent` type names** — use `Scope` / `Workflow` (and `ScopeStatus` / `WorkflowStatus`, `WorkflowType`, etc.). `Skill` and `Agent` remain as aliases for Release N.
- **OpenAPI `SkillDto` / `AgentDto`** — prefer generated `ScopeDto` / `WorkflowDto` (same shape; legacy names marked deprecated in the spec).
- **List/deploy response envelope keys** — list endpoints prefer `scopes` / `workflows`; deploy responses prefer `scope` / `workflow`. Deprecated `skills` / `agents` / `skill` / `agent` keys are still accepted when the canonical key is absent.
- **`conversation_skill_id()`** — use `conversation_scope_id()`. `client.modus.conversations.list(kind=...)` accepts `scopes` (canonical) or deprecated `skills`.

### Changed

- SDK read types are now exported as `Scope` / `Workflow` backed by generated `ScopeDto` / `WorkflowDto`.
- Custom context create responses always expose `.uid` (same value as `contextItemId`).

### Removed

- `ModusManagement.organization.delete()` — organization deletion is no longer
  part of the public API / PAT surface (SPA-only).

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
