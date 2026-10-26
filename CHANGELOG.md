# Changelog

Published versions come from the `sdk-python/v*` tags; the current release is
whatever [PyPI](https://pypi.org/project/modus-sdk/) is serving. This file records
what changed, not which version is live.

Record concise, customer-visible release notes under `[Unreleased]` for every SDK
release, including pre-1.0 (`0.x`) releases.

## [Unreleased]

### Added

- **`deepseek-v4.1-flash-1017` model.** The October 17, 2026 snapshot of DeepSeek V4.1 Flash is an
  accepted chat model id.
- **Async scope evaluations.** `AsyncModusManagement().scopes.evaluations(id)` has the same methods as the sync client: `get_config`, `update_config`, `trigger_run`, `list_runs`, `get_run`, `add_case`, `update_case`, and `delete_case`.

### Changed

- **Breaking (pre-1.0): evaluation run timestamps are `datetime`.** `EvaluationRun.started_at` was a `str` and is now a timezone-aware `datetime`. `finished_at` is `datetime | None`. Replace string parsing with the value itself. Use this release with a Modus API that sends ISO 8601 evaluation timestamps; an older server's JavaScript date string fails validation.
- **Breaking (pre-1.0): scope `connectionSet` rows have one shape.** `scopes.create` and `scopes.update` accept each entry only as `{ connection_id, path, preferences?, context_enabled? }`, where `path` is an array of strings, `preferences` an object and `context_enabled` a boolean. An empty path selects the whole connection. Any other field, a non-string path segment, an empty or null `connection_id`, or a null `connectionSet` is rejected with 400. `variation.connection_set` entries are now `ConnectionSetItemDto` models (`.connection_id`, `.path`, `.preferences`, `.context_enabled`); `row["connection_id"]` no longer works.
- **Breaking (pre-1.0): workflow `guardrails` removed.** `workflows.create` and `workflows.update` (sync and async) no longer take `guardrails=`. The workflow access configuration has no guardrails, so every call that set it failed with 400 and changed nothing. Scope `guardrails` are unchanged.
- **Breaking (pre-1.0): `scopes.memories(id).update()` returns `None`.** The server answers 204 with no body; the method raised a `ValidationError` after the update had been applied.
- **Breaking (pre-1.0): `manager_id` is an `int`.** `scopes.update(manager_id=...)` takes the numeric id of the manager scope. It was typed `str`, which the server rejects with 400. To detach, pass `update_mask="managerId"`.
- **Breaking (pre-1.0): evaluation runs `page_size` is checked.** `mgmt.scopes.evaluations(id).list_runs()` rejects a `page_size` outside 1..100 with 400, like every other list (it was clamped above 100).
- **Breaking (pre-1.0): `runs.interrupt` and `runs.edit_queued` take the turn to send.** `runs.interrupt(run_id, next_run, *, last_seen_event_id=None)` and `runs.edit_queued(run_id, next_run)` send `next_run` (`message` and `sessionId`, the run's conversation id) as `nextRun` and return the admitted run as `RunAdmission` (`run_id`, `status`), sync and async. For `interrupt`, that is the new run that carries the follow-up turn; stream it with `runs.stream(run_id)`. The old optional `body` defaulted to `{}`, which the server always rejected, and the methods returned `None`. `interrupt` sets `nextRun.runId` when you omit it, so a retried request returns the same run instead of starting a second turn. On a run that has already finished, `interrupt` starts a follow-up turn.
- **`runs.resume` requires `sessionId` and sends no message.** A missing or blank `sessionId` raises `ValueError` before any request; it was replaced by a random id, so the server answered "no longer pending". The documented example sends only `decision` and `sessionId`; a non-empty `message` is rejected by the server.

### Fixed

- **Completed evaluation runs could not be listed or read.** `mgmt.scopes.evaluations(id).list_runs()` and `.get_run(run_id)` raised `ValidationError` for any finished run, because `avg_score`, `finished_at` and the result fields `actual_output`, `passed`, `score`, `reasoning` and `was_passing_before` were typed as dicts. They are now `float`, `datetime`, `str` and `bool`, each optional. The server now sends evaluation timestamps as ISO 8601 (see Changed). An evaluation recipient's `name` is `str | None`.
- **A path id of `'..'` could target the parent resource, e.g. delete the scope.** `scopes.memories(7).delete('..')` sent `DELETE /scopes/7`. Every path id that is blank, `'.'` or `'..'` now raises `ValueError` before any request; a blank id no longer returns the list page as one item.
- **Paging no longer skips items.** `scopes.list()`, `workflows.list()`, `connections.list()` and their auto-paging iterators return every item: a page boundary no longer drops items created in the same millisecond, and `connections.list()` no longer drops a connection or ends early when other members' connections are hidden from you.
- **Numeric ids above 2147483647 return 404.** Such a scope or workflow id now raises `NotFoundError` instead of a 500 that was retried three times.
- **Evaluation runs page in a stable order.** Runs that started at the same time are no longer repeated or skipped across pages.
- **`update_mask` sends only what you set.** `scopes.update`, `workflows.update`, `context.items.update`, and `workflows.interfaces(id).update` sent `null` for every unset field whenever `update_mask` was given, and the server rejected the call with 400. The body now holds the fields you set, plus `null` for each field the mask names and you left unset, which the server clears.
- **`Toolset.empty()` clears a scope's tools.** `scopes.update(toolset=Toolset.empty())` sends `{}`; it was dropped, so the tools stayed.
- **`suggestions.list(scope_ids=[])` raises `ValueError`** before any request. It sent `scopeIds=`, which the server rejects with 400.
- **Docs: ids are numeric.** The getting-started example took a slug (`scopes.get("revenue-analysis")`), which the server rejects with 400; it now takes an id from `list()`. Docstrings no longer say "id or slug". `type="task"` is documented as a deprecated alias on create; `workflows.update` accepts only `"workflow"`.

## [0.9.0] — 2026-10-24

### Added

- **List selectable units.** `client.connections.list_selections(connection_id)` and
  `iter_selections(connection_id)` page the units a scope can select on a connection
  (`GET /connections/{id}/selections`). `client.connections.list()` items may include
  `selection_model`.
- **Evaluation case methods.** `mgmt.scopes.evaluations(id).add_case()`, `.update_case(case_id)`, and `.delete_case(case_id)` add, change, or remove one evaluation case. Omit `id` on add and the client assigns one, so a retry sends the same id. A retry whose id is already stored returns a conflict; an identical body is not treated as success. An empty `task` is allowed. An update with neither field is rejected.

### Changed

- **MCP config is checked on write.** Scope create, scope update, and `PATCH /scopes/{id}/mcp-config` return the effective core tools and tool exposure. A changed value must use true or false for each core tool, and version 1 with mode subset or discovery for tool exposure. A newly added exposure key must be one the scope can expose. A key already stored can be sent again or removed.
- **Breaking (pre-1.0): typed evaluation cases.** `PATCH /scopes/{id}` replaces `evaluations` with objects of `id` (optional), `task`, and `expectedOutput`. `task` and `expectedOutput` are required, and any other key, such as `createdAt` or `updatedAt`, is rejected with 400. Omit `id` on a new case and one is assigned. A repeated `id` is rejected. An empty `task` is allowed.
- **Breaking (pre-1.0): scope `interfaces` have one shape.** `scopes.create` and `scopes.update` (`POST /api/v1/scopes` and `PATCH /api/v1/scopes/{id}`) accept only MCP interface rows. `type` must be `mcp`. Each row has an optional id and name and a config of core tools and exposed integrations. A row without an id or name is assigned one. Responses return only id, type, name, and config; extra stored keys such as `enabled` are no longer returned.
- **Breaking (pre-1.0): workflow responses declare their shapes.** `Workflow.variation.trigger`, `workflow_structure`, and `agent_selection` are `WorkflowTriggerResponseDto`, `WorkflowStructureResponseDto`, and `AgentSelectionResponseDto` instead of dicts. Replace dict indexing with attribute access: `agent_selection["model"]` becomes `agent_selection.model`, and `trigger["schedule"]` becomes `trigger.schedule`. A non-schedule trigger has `schedule: null`, and a schedule leaves unused cadence fields null. A workflow interface `config` describes Slack and Teams (`accessMode`, `allowedEmails`, `availableChannelIds`) and an empty object for MCP.
- **Scope `connectionSet` rows must be a selectable unit.** `scopes.create` and `scopes.update` reject a new row whose path is neither the whole connection nor one selectable unit of it, with 422 `root.not_a_root`. A row already stored can stay, and removing it still succeeds.
- **Workflow interface config.** Slack and Teams `config` on a workflow interface is `accessMode` (`all`, `allow-list`, or `allow-org`), `allowedEmails`, and `availableChannelIds`. An MCP interface accepts no config keys. An unknown key or invalid value in a changed config returns 422 with violations; `config: null` returns 400. Unchanged stored values are accepted.
- **`search_query` documents word search.** `mgmt.context.custom_items.list(search_query=...)` (`GET /context/custom-items`) describes
  word search: it returns rows that contain every word of the query, case-insensitive.
- **Known toolset values are validated.** A new or edited scope `toolset` value must match that tool's shape.
  Most tools take an array of strings. `file_publish` takes `{ actions: string[], rules?: { nameMode: "any" | "restricted", allowedNames: string[] } }`.
  Coding tools take an array of `{ connectionUid, repoOwner, repoName, branch }`.
  `sql_runner` entries are `VERB:connectionId:`, optionally followed by `database:schema`, where `VERB` is `SELECT`, `INSERT`, `UPDATE`, `DELETE`, or `CREATE`.
  A value that does not match is `422`
  with rule `toolset.bad_value`; an unknown key stays `toolset.unknown_key`. Sending the same stored value again succeeds,
  including a historical value the new check would reject, and removing that value succeeds. The handwritten `Toolset` helpers are unchanged.

### Fixed

- **Workflow GET triggers and permission reasons.** `parse_trigger` accepts the trigger on a workflow response and still sends snake_case keys (`trigger_type`, `time_of_day`) on update. `Workflow.manage_denial` is again the string `not_owner`, `needs_group_manage`, or `null`.
- **Model settings survive a workflow update.** `AgentSelection` carries `model_settings`, and `parse_agent_selection` keeps it, so a selection read from a workflow and passed to `workflows.update(agent_selection=...)` no longer clears the stored `modelSettings`.

### Removed

- **`ToolsetDto` and `ToolsetToolDto`.** Scope create and update `toolset` is a map of tool key to its configuration. The generated `{ tools: [{ id, enabled, config }] }` models are gone. Unknown keys are rejected. The handwritten `Toolset` helpers are unchanged.
- **Breaking (pre-1.0): evaluation case timestamps.** Scope evaluation cases no longer include `createdAt` or `updatedAt`.

## [0.8.0] — 2026-10-18

### Removed

- **Breaking: evaluation Slack `nangoConnectionId`.** Send `connectionId`, the
  Slack connection's Modus UUID, in notification settings instead. Generated
  models expose `connection_id` (UUID) instead of `nango_connection_id`; JSON
  requests use `connectionId`. No deprecation window; requires a major release.

### Added

- **Service account tokens.** `api_key` accepts an organization-owned service account
  token (`modus_sat_<orgUuid>_<prefix>_<secret>`) as well as a personal access token.
- **`include_own_learnings` on `scopes.create`.** A new scope reads what is taught while
  using it by default; pass `False` to create it without its own learnings.
- **`default_headers` client option.** `Modus`, `AsyncModus`, `ModusManagement` and
  `AsyncModusManagement` accept headers to send on every request. They override the
  SDK's own defaults, except `Authorization`, which always comes from `api_key`.
- **`X-Modus-Client: sdk` request header.** Every request names the SDK as the client.
- **`gpt-6-luna` model.** The chat request `model` enum
  (`Model.gpt_6_luna`) accepts the new OpenAI model.
- **`gpt-5.6-luna` model.** The chat request `model` union accepts the new
  OpenAI model.
- **Move Files items.** `mgmt.context.items.move(uid, destination_folder_uid=...)`
  relocates a live file or folder. Pass `None` for the Files root.
- **Generic context item browse.** `client.context.items.list` and
  `mgmt.context.items.list` accept optional `connection_ids`, `parent_uids`,
  and `ancestor_uids` arrays. Omit a filter to leave it unrestricted; pass
  `[]` for the known-empty / match-none forms. Async twins match.
- **Upload destinations.** Sync and async upload helpers accept an optional
  `folder_path` prefix for single files, batches, and directories.

### Changed

- **Scope context file handling.** `scopes.get_context` returns bounded inline
  previews for large bodies; full file content is not available through this REST method.
- **Connected-integration toolset entries bind to a connection.** A scope toolset entry
  given as `{"actions": [...], "rules": ...}` (what `Toolset.integration` and its
  shortcuts build) is bound on create/update to the organization's newest workspace
  connection of that integration and returned as `{"byConnection": {<connection id>:
  {...}}}`. A create or update whose entry has no workspace connection to bind to
  returns `422`; re-sending an entry already stored unchanged is accepted.
- Deleting a Files folder through context items also deletes its contained files,
  subfolders, and parsed file items.

## [0.7.0] — 2026-09-30

### Added

- **Scope Slack/Teams interfaces.** `scopes.interfaces(scope_id)` lists, adds, updates and
  removes the Slack and Microsoft Teams interfaces of a scope (sync and async).
- **`claude-sonnet-5.5` model.** The chat request `model` enum
  (`Model.claude_sonnet_5_5`) accepts the new Anthropic model.
- **`deepseek-v4-pro`, `deepseek-v4-flash-latest`, and `kimi-k3` models.** The
  chat request `model` enum accepts these models.
- **Optional `ancestry` on context items.** List, get, lookup, and custom-item
  responses may include ordered ancestors (`uid`, `display_name`, `type`). The
  field is omitted on older responses, `null` when stored ancestry is unknown,
  and `[]` when the item has no ancestors.
- **`context_item_uids` on composed context.** `POST /modus/context` and
  `POST /scopes/{id}/context` now return the UIDs of the context items the composer
  kept, in selection order. Previously the response reported `selectedCount` with no
  way to learn which items it counted — `context_items` has been an empty array for
  some time and remains deprecated.
- **`claude-opus-5.5` and `grok-4.7` models.** The chat request `model` enum
  (`Model.claude_opus_5_5`, `Model.grok_4_7`) accepts the two new models.

### Removed

- **`RunConfigDto.strategies`.** The run API no longer publishes context-composer
  strategy IDs, so the generated `RunConfigDto` model no longer carries
  `strategies`. These IDs are the composer's internal vocabulary and get renamed,
  so a pinned value could silently stop doing anything. Strategy selection is
  chosen by the service.

### Added

- **Dashboard documents.** `mgmt.context.dashboards` document operations: list, get, create,
  update_draft, publish, delete, versions, draft snapshots, access, ownership transfer
  (`list()`, `get()`, `create()`, `update_draft()`, `publish()`, `delete()`,
  `list_versions()`, `get_version()`, `restore_version()`, `list_draft_snapshots()`,
  `update_access()`, `request_ownership_transfer()`, `accept_ownership_transfer()`,
  `cancel_ownership_transfer()`). New types `DashboardVersion`, `DashboardDraftSnapshot` and
  `DashboardPublishResult`; version definitions are returned as stored, so older versions
  may lack newer fields. Async twins are on `AsyncModusManagement`.

- **Dashboard draft elements and layout.** `mgmt.context.dashboards.elements(dashboard_id)`
  lists, reads, creates and updates the tiles and filters of a dashboard draft
  (`list()`, `get()`, `create()`, `update()`), and `mgmt.context.dashboards.update_layout()`
  moves or resizes several of them in one change. Every write takes the `expected_revision`
  it is based on and raises `ConflictError` when the draft changed. Async twins are on
  `AsyncModusManagement`.

- **Workflows linked to a dashboard alert.** Workflow responses carry `dashboard_alert`
  (`dashboard_id`, `tile_id`) when a dashboard KPI alert generated the workflow. Updating the
  name, trigger or workflow structure of such a workflow raises `ConflictError` unless the update
  sets `disconnect_dashboard_alert=True`, which disconnects it from the alert.

- Ingested-data uploads accept an optional source HTTP `response.status` from 100 through 599.

- **Ingested data uploads.** `Modus.ingested_data.upload` and
  `AsyncModus.ingested_data.upload` store raw SQL or HTTP request-response exchanges.
  Uploading identical content again raises `ConflictError`.

- **Conversation lists: optional `source` and `source_ref` filters.** `client.modus.conversations.list`
  and `client.scopes.conversations(scope_id).list` (both sync and async) now accept `source`
  to restrict results to one UI surface (e.g. `"context_chat"`, `"dashboard_copilot"`,
  `"dashboard_assistant"`, `"slack"`) and `source_ref` to narrow `source` to one instance of
  that surface — for `dashboard_copilot` and `dashboard_assistant`, a single dashboard id.
  `source_ref` requires `source`; sent on its own it is rejected with a 422. On the org-level
  list, `source` may only be combined with an omitted `kind` or `kind="all"` (not
  `kind="modus"` / `kind="scopes"`). Conversations recorded before the filter shipped carry
  no instance key and do not match it.

- **File uploads: optional `folder_path`.** `upload_from_url`, `finalize`, and directory
  uploads now accept an optional relative folder label that is stored with the file and
  returned on the file resource. `upload_dir` sets it automatically from each file's path
  relative to the upload root, so directory structure is preserved.

### Changed

- **Scope interfaces are MCP-only.** `management.scopes.create` and
  `management.scopes.update` accept only `interfaces` entries with `type: "mcp"`;
  any other type (for example `slack` or `teams`) is rejected with HTTP 400.
  Manage a scope's Slack and Teams interfaces with `scopes.interfaces(scope_id)`.

- **Scope MCP: Get Answer works alone.** `management.scopes.patch_mcp_config` now
  rejects a config that turns `core_tools.chat` (`get_answer`) on together with
  `getContext`, `teachModus` or any tool exposure, with HTTP 422. The call replaces the
  whole config and omitted keys take their defaults: `chat` off, `getContext` on,
  `teachModus` off, every tool exposed. To turn Get Answer on, send `chat: true`,
  `getContext: false` and an empty `subset` exposure in one call.

- `modus.get_context` and `scopes.get_context` now apply `limit` to composed
  context items, including normal Markdown responses. Omitting it remains unlimited.

- **Breaking (pre-1.0):** Ingested-data upload results now contain only `checksum`;
  object keys are internal storage details.

- **Breaking (pre-1.0):** Directory-managed member groups no longer include member IDs.
  Use the member count to determine their size. Native member groups are unchanged.

## [0.6.0] — 2026-08-15

### Changed

- Public OpenAPI updates from production release.

## [0.5.0] — 2026-08-08

### Changed

- Public OpenAPI updates from production release.

## [0.4.0] — 2026-08-01

### Changed

- Public OpenAPI updates from production release.

## [0.3.0] — 2026-07-26
