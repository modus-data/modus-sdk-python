# Changelog

**Current release:** `0.1.5` on [TestPyPI](https://test.pypi.org/project/modus-sdk/).

## [Unreleased]

### Changed

- Generated models and operation registry no longer embed monorepo codegen instructions; field help text in `_generated/models.py` is sanitized for the public mirror (no `AIP-158` or REST route callouts in IDE tooltips).

### Added

- Context ergonomics (Tier B/C): `mgmt.context.update_note()`, `update_link()`, and `update_saved_query()` — paired with the existing `create_*` helpers; merge server-owned `content` fields for you. Read accessors on `modus`: `note_title`, `note_body`, `link_title`, `link_url`, `saved_query_name`, `saved_query_sql`, `context_item_label`, `is_verified`. Sync and async.
- HTTP implementations on `ModusManagement` for all remaining public contract operations: semantic context creators (`create_dimension`, `create_fact`, `create_metric`, `create_filter`), skill/agent ownership and undelete, skill MCP config and version history, usage metrics (`mgmt.usage.list()`), and organization deletion (`mgmt.organization.delete()`). Sync and async.
- `sdk-python-sync` skill, `coverage-gaps.py`, and `openapi-diff-summary.py` for OpenAPI-aligned SDK maintenance; GitHub Action to spawn a Cursor cloud agent when a merged PR changes `openapi/v1.json` on `develop`, poll until finished, and Slack-DM the sync PR link to the SDK owner.

- `client.connections.list()` / `find(name=...)` — discover integration connections (`id`, `name`, `type`) for saved-query and context workflows. Sync and async.
- `view` and `manager_id` filters on `client.skills.list()` / `mgmt.skills.list()`; `view` on `get()`.
- `view` and `include_variation` filters on `client.agents.list()` / `mgmt.agents.list()`; `view` on `get()`.
- `Toolset` builders for attaching tools to a skill: `Toolset.slack(...)`, `Toolset.clickup(...)`, and other integrations, plus `Toolset.sql_runner(...)`, `Toolset.memory()`, and `Toolset.custom_mcps(...)`. Combine several with `Toolset.combine(...)` or `.merge(...)`.
- `client.context.items.list_values_for(item, content_key_path)` — list a field's values straight from a `ContextItem` without repeating its `uid` and `context_type`.
- `search` filter on `client.skills.list()` / `mgmt.skills.list()` and `client.agents.list()` / `mgmt.agents.list()` — case-insensitive substring match on the name.
- `type` filter on `client.agents.list()` / `mgmt.agents.list()` — return only `"task"` or `"workflow"` agents, with editor autocomplete.
- `guardrails=` on `mgmt.skills.create` / `update` and `mgmt.agents.create` / `update` — set runtime guardrail labels without exposing ACL configuration.

### Changed

- **Breaking:** Read types (`Skill`, `Agent`, `ContextItem`, …) are now re-exported OpenAPI DTOs from `modus._generated.models` — full API shape on every GET, including `variation`, `access_config`, `org_uuid`, and permission fields (`can_manage`, `can_use`, `manage_denial`). Consumption and management share the same read types; use `skill.variation.instructions` instead of top-level `skill.instructions`. `ChatResult.content` replaces `.text`. Status helpers (`is_active`, `is_draft`) are removed — compare `status == "active"` or `status == "draft"`.
- **Breaking (`Skill`):** `Skill` is `SkillDto` (full GET shape: `access_config`, `variation`, `pending_ownership_transfer`, permission fields). `SkillStatus` is now the generated `Status1` enum (not `Literal["draft", "active", "deleted"]`). `SkillVariation` aliases `SkillVariationDto`; `AccessConfigDto` is newly exported. Migrate string comparisons / pattern matching on status accordingly.
- **Breaking (`ContextItem`):** `ContextItem` is `ContextItemDto` (full GET shape: `user_feedback`, `topics`, `connection_id`, `selection_id`, `data_path`, `last_update_metadata`, …). `ContextType` is now `str` (was a `Literal[...]` union). New exports: `ContextItemLookupRow` (`LookupContextItemRowDto`) and `ContextItemDeletion` (`DeleteContextItemResponseDto`). `context.items.lookup()` returns `Optional[ContextItemLookupRow]` (uid, context_type, data_path, content, connection_id, selection_id) — not full `ContextItem`.
- **Breaking (`AgentRun`):** `client.agents.runs.get()` / `AgentRun` expose `source` (`"live-query"` or `"history"`) instead of the old handwritten `history` field. Update callers that read `AgentRun.history` to `AgentRun.source`.
- **Breaking:** Removed hand `modus/_wire/` and read `_translate.py` modules; HTTP uses `invoke_operation` for all non-streaming routes.
- **Breaking:** Removed `FeatureNotReadyError` and the PREVIEW tier. Every public operation now calls the API; backend errors (e.g. `UnprocessableError` on 422) pass through with the server message.
- `operation_coverage.py` uses a single `OPERATIONS` map (no WRAPPED/PREVIEW split).
- **Breaking:** `client.skills.get_context()` returns `SkillContextComposition.context` (composed markdown string) instead of `context_items`. `limit` applies only when the API falls back to structured JSON.
- **Breaking:** skill conversations are now scoped per skill: use `client.skills.conversations(skill_id).list()` / `.get(thread_id)` (previously `conversations.list(skill_id)`). This matches `mgmt.skills.memories(skill_id)`.
- `mgmt.agents.create(type=...)` now accepts `"task"` or `"workflow"` with editor autocomplete.
- `client.agents.runs.list(...)` documents the accepted `status`, `timeframe`, and `approval_scope` values and surfaces them as editor hints.
- Clearer error message when an unsupported chat `model` is passed.
- `mgmt.skills.update(...)` now accepts `evaluations` and `supervision_subordinate_descriptions`.
- `mgmt.agents.update(...)` now accepts `type` (change an agent between `"task"` and `"workflow"`).
- `mgmt.skills.update`, `mgmt.agents.update`, and `mgmt.context.items.update` now accept `update_mask` to explicitly clear fields.
- `mgmt.context.create_saved_query(...)` makes `query` optional, matching the API.
- `ContextItem.created_at` / `updated_at` are now optional. They are returned by `list()`/`get()` and omitted by `lookup()`.
- Typed write inputs are now the only accepted form: `toolset`, `trigger`, and `agent_selection` require their builder/model (for example `Toolset.slack(...)`, `AgentTrigger.manual()`); passing a raw `dict` now raises a clear `TypeError`. Genuinely free-form JSON fields (`workflow_structure` and `JsonObject` blobs such as `connection_set`, `interfaces`, and `evaluations`) still accept a plain `dict`.

### Fixed

- `client.context.items.lookup(...)` no longer raises when the matched item has no timestamps.
- `mgmt.context.items.update(...)` now matches the API contract. It previously sent `title` and `verificationStatus`, which the server rejects with `400`. Use `content`, `context_type`, `description`, `user_feedback` (`"positive"`/`"neutral"`/`"negative"`), and `topics` instead.
- `update_mask` now actually clears fields. On `mgmt.skills.update`, `mgmt.agents.update`, and `mgmt.context.items.update`, naming a field in `update_mask` and leaving its argument unset now sends `null` for that field (previously it was dropped, so the clear never happened).
- Input validation fails fast on obvious mistakes: an empty/whitespace `update_mask`, a blank `thread_id` in `conversations.get(...)`, and passing a bare string (instead of a list) to `Toolset.sql_runner`/`custom_mcps`/integration factories now raise `ValueError` before any request is made.
- `mgmt.agents.create` / `update` with `agent_selection=` now serializes inner entries with `agent_id` and `priority_order` (snake_case). Previously `agentId` / `priorityOrder` were sent and the API rejected the body with `400`.

### Removed

- **Breaking:** removed `AccessConfig` and the `access_config=` parameter on `mgmt.skills` / `mgmt.agents` create and update. Use `guardrails=` to set runtime guardrail labels; ACL fields (`visibility`, sharing) are not exposed until typed factories ship.
- **Breaking:** removed the non-functional `Toolset(tools=[...])` / `Toolset.from_tools(...)` write path and the `ToolsetTool` type. Use the `Toolset` builders above.
- Removed the `s3_key` field from `CreatedContextItem` (consumption and management). Use `context_item_id` with `client.context.items.get(...)` for the full item.
- Removed `org_id` from `ContextItem`. Your API key is already scoped to one organization, so the field carried no information.

## [0.1.5] — 2026-06-04

TestPyPI (`sdk-python/v0.1.5`).

### Changed

- README: product-oriented intro (context layer, two clients); removed internal API reference and capability matrix.
- Examples and PyPI package description aligned with the same product framing (no internal API paths in example docs).
- Replaced long example guides with thin scripts (`quickstart.py`, `chat.py`, `manage_skill.py`); Streamlit demo branding pass (logo, theme).
- Contributor conventions updated for TestPyPI README policy (no Swagger on PyPI).
- README copy tightened for first-time users (bullet walkthrough, approachable two-client prose; no docs URL or hosting details).

## Prior releases

0.1.0–0.1.4 — TestPyPI pre-releases: consumption + management clients, examples, trigger serialization fix, ownership transfer fields, README logo/badges.
