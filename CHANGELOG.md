# Changelog

**Current TestPyPI release:** [`0.1.7`](https://test.pypi.org/project/modus-sdk/) (2026-06-16). Production PyPI not yet published.

## [Unreleased]

### Changed

- **BREAKING: `client.scopes` / `client.workflows` and `mgmt.scopes` / `mgmt.workflows` are now canonical** (sync + async). They call the canonical `ScopesController_*` / `WorkflowsController_*` / `ScopeRunsController_*` / `WorkflowRunsController_*` operationIds against the `/api/v1/scopes` and `/api/v1/workflows` routes. Read types are unchanged (`Skill`, `Agent`). The subordinate scope-run helper is now `client.workflows.runs.create_scope(scope_id, body)` (was `create_skill`).
- Generated `ModusChatRequestDto.message` is optional (omit when `approvalContinuation` is true), matching the public OpenAPI spec synced in #2907.
- Generated models now mirror the pruned public OpenAPI schema set, removing internal-only orphan DTOs and reflecting non-nullable `slug` / `createdAt` fields as required strings.
- **MCP `get_context_item`** — preview and full modes only; removed grep/range. Large files (>96KB) default to preview; follow up with `mode: "full"` on the same `sessionId` and path.
- Public model **descriptions/docstrings** now use the canonical **Scope** / **Workflow** vocabulary (were Skill / Agent). Text-only — no field, type, method, or `Skill`/`Agent` type-name changes; regenerated from the updated OpenAPI descriptions.

### Added

- **`claude-sonnet-4.6`** restored as an allowed run `model` value (scope/workflow run creation and chat).
- **`selectedCount`** on scope and Modus context compose responses (REST + MCP `get_context`).
- `conversations(scope_id).get()` (sync + async) accepts optional `message_limit` / `before_message_index` kwargs to request a bounded message window; the response gains an optional `message_window` field describing the returned slice. Omit both for the full conversation (unchanged default behavior).
- **`client.suggestions`** (sync + async) — `list()` returns approved suggested questions (optional `skill_id(s)` filter), `record_event()` records an impression/click/dismiss event against a suggestion.
- **`client.workflows.runs.active()` / `active_by_session(session_ids)`** (sync + async) — list active (queued/pending/running) conversation runs for the current user, or look up active runs for specific conversation thread ids.

### Removed

- **BREAKING: `client.skills` / `client.agents` and `mgmt.skills` / `mgmt.agents`** (sync + async) — the legacy accessors are removed in favour of `client.scopes` / `client.workflows` and `mgmt.scopes` / `mgmt.workflows`. Migrate `client.skills.*` → `client.scopes.*`, `client.agents.*` → `client.workflows.*`, `client.agents.runs.create_skill(...)` → `client.workflows.runs.create_scope(...)`.
- **BREAKING: legacy operationIds** `SkillsController_*`, `AgentsController_*`, `SkillChatController_*`, `SkillContextController_*`, `ConversationsController_*`, `MemoriesController_*`, `AutomationRunsController_*`, `SkillRunsController_create`, and `AgentRunsController_create` are no longer referenced; the SDK targets the canonical `Scopes*` / `Workflows*` / `Scope*` / `WorkflowRuns*` operationIds.
- **`CreateDimensionDto` / `CreateFactDto` / `CreateFilterDto` / `CreateMetricDto`** and the corresponding `dimension` / `fact` / `metric` / `filter` values on the context creator `Kind` enum — the backing `/api/v1/context/{dimensions,facts,metrics,filters}` endpoints were unimplemented public stubs and have been removed server-side (CU-86ey1251z). No SDK method ever called these; this is a generated-type-only removal.

## [0.1.7] — 2026-06-16

### Added

- **`client.modus`** — native Modus assistant (`chat`, `chat_stream`, `get_context`, `conversations` with `kind` filter). Org-wide full-environment access; not `skills.chat(0)`.
- Shipped example `examples/scripts/modus_chat.py`.

### Changed

- README: Modus vs skills guide, `client.modus` usage (follow-up threads, streaming, context compose, conversations), and `result.content` fixes.
- Dev examples: `modus_chat_demo.py`, `async_modus_chat.py`; skill chat example docstrings updated for public streaming.

## [0.1.6] — 2026-06-15

### Added

- Full **Modus** and **ModusManagement** API coverage (sync + async): skills, agents, chat, context, runs, connections, usage metrics, org admin.
- Context update helpers and read accessors; `Toolset` builders; list filters (`search`, `view`, `type`, `manager_id`); `guardrails=` on skill/agent writes.

### Changed

- Read types match API responses (`Skill`, `Agent`, `ContextItem`, …); early TestPyPI callers may need small updates (e.g. `skill.variation.instructions`, scoped `conversations(skill_id)`, `get_context().context`).
- Typed builders required for toolset, trigger, and agent selection.
- Usage metrics: `model` optional when grouped by skill, agent, or interface (use `group_value`). **Compatibility:** corrects 0.1.5 where `model` was incorrectly required on all breakdowns.
- **Renamed** `skills.undelete()` → `skills.restore()` and `agents.undelete()` → `agents.restore()` (sync + async).

### Fixed

- Context updates, `update_mask` clearing, agent selection payloads, and input validation.

### Removed

- Preview/stub operations; `access_config=` on writes (use `guardrails=`); legacy `Toolset(tools=[...])`.
- **`agents.chat()` and `agents.chat_stream()`** — buffered agent chat is no longer part of the public API; skill chat (`skills.chat()` / `skills.chat_stream()`) is unaffected.

## [0.1.5] — 2026-06-04

- Product-focused README and examples (`quickstart.py`, `chat.py`, `manage_skill.py`); Streamlit demo branding.

## Prior releases

| Version | Summary |
|---------|---------|
| 0.1.0–0.1.4 | Initial TestPyPI builds: consumption + management clients, examples, trigger fix, ownership transfer fields, README badges. |
