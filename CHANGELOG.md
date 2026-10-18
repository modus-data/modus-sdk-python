# Changelog

Published versions come from the `sdk-python/v*` tags; the current release is
whatever [PyPI](https://pypi.org/project/modus-sdk/) is serving. This file records
what changed, not which version is live.

Record concise, customer-visible release notes under `[Unreleased]` for every SDK
release, including pre-1.0 (`0.x`) releases.

## [Unreleased]

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
