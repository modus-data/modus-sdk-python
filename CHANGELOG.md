# Changelog

Published versions come from the `sdk-python/v*` tags; the current release is
whatever [PyPI](https://pypi.org/project/modus-sdk/) is serving. This file records
what changed, not which version is live.

Record concise, customer-visible release notes under `[Unreleased]` for every SDK
release, including pre-1.0 (`0.x`) releases.

## [Unreleased]

### Added

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
