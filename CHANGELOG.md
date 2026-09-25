# Changelog

Published versions come from the `sdk-python/v*` tags; the current release is
whatever [PyPI](https://pypi.org/project/modus-sdk/) is serving. This file records
what changed, not which version is live.

Record concise, customer-visible release notes under `[Unreleased]` for every SDK
release, including pre-1.0 (`0.x`) releases.

## [Unreleased]

### Added

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
  `"slack"`) and `source_ref` to narrow `source` to one instance of that surface — for
  `dashboard_copilot`, a single dashboard id. `source_ref` requires `source`; sent on its
  own it is rejected with a 422. On the org-level list, `source` may only be combined with
  an omitted `kind` or `kind="all"` (not `kind="modus"` / `kind="scopes"`). Conversations
  recorded before the filter shipped carry no instance key and do not match it.

- **File uploads: optional `folder_path`.** `upload_from_url`, `finalize`, and directory
  uploads now accept an optional relative folder label that is stored with the file and
  returned on the file resource. `upload_dir` sets it automatically from each file's path
  relative to the upload root, so directory structure is preserved.

### Changed

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
