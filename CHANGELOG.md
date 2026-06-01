# Changelog

All notable changes to the Modus Python SDK are documented here.
Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/)
Versioning: [SemVer](https://semver.org/)

## [Unreleased]

### Changed

- List pagination uses Google AIP-158 throughout: `page_size` / `page_token` on
  list methods, `pageSize` / `pageToken` on the wire, `Page.next_page_token`
  from `nextPageToken`. Applies to `skills.list`, `skills.conversations.list`,
  and management mirrors.

### Added

- `client.skills.chat()` and `client.skills.chat_stream()` — buffered and SSE chat
  against public `POST /api/v1/skills/{id}/chat` (and conversation continue paths).
- `client.skills.get_context()` — context composition via
  `POST /api/v1/skills/{id}/context` (RAG query, no LLM).
- `client.agents.chat()` and `client.agents.chat_stream()` — same chat surface for agents.
- `client.agents.runs.list()` and `client.agents.runs.get()` — agent run history.
- Public types: `ChatResult`, `SkillContextComposition`, `AgentRun`, `AgentRunListItem`,
  stream events (`TokenEvent`, `DoneEvent`, …), `RunCancelledError`, `StreamTimeoutError`.
- Async parity on `AsyncModus` for all new methods.
- Example: `sdk/python/examples/chat_demo.py`.

### Changed

- `DoneEvent` and SSE parser now carry `thread_id` from the `done` frame.
- Error SSE frames may use an `error` field (OpenAPI `SkillChatErrorEventDto`).

## [0.1.3] — 2026-05-31

Bugfix release: align list pagination with modus-api AIP-158 (tag `sdk-python/v0.1.3`
when publishing). Latest tagged release before this is `sdk-python/v0.1.2`.

### Fixed

- List endpoints (`skills.list`, `agents.list`, `context.items.list`,
  `context.items.list_values`, and management mirrors) now send AIP-158
  `pageSize` / `pageToken` and parse plural response keys (`skills`, `agents`,
  `contextItems`, `values`, `nextPageToken`). Fixes `400` errors against
  modus-api after PR #2252.
- `context.items.lookup` parses `{ "item": … | null }` responses (no match
  returns `None` instead of raising validation errors).
- Examples `list_skills.py` / `list_agents.py` use `ModusManagement` for
  configuration detail (timestamps, variation fields).

### Changed

- All paginated list methods (`skills.list`, `agents.list`, `context.items.list`,
  `skills.conversations.list`, management mirrors, etc.) use `page_size` and
  `page_token` (AIP-158 `pageSize` / `pageToken` on the wire). `Page.next_page_token`
  maps from `nextPageToken` for iteration.
- `validate_limit` renamed to `validate_page_size` (`list_values` enforces
  max page size 200 client-side).
- Context item list filter sends `contextTypes` (array) per OpenAPI.

### Added

- `tests/test_openapi_list_operations.py` — guards list query params against
  `openapi/v1.json` (rejects non-AIP `limit` / `cursor` on list calls).
- `tests/examples/test_example_imports.py` — `run_all.sh` scripts exist; examples
  avoid management-only fields on consumption types.
- `tests/integration/` — optional `-m integration` live API smoke tests.
- Examples: `run_all.sh` auto-loads monorepo env/venv; per-script timing; heartbeat
  in full mode only.

## [0.1.2] — 2026-05-28

### Changed

- Management surface is now shipped inside `modus-sdk` as
  `modus.management.ModusManagement` (previously the separate
  `modus-management` package). One install, one version, unified
  `modus.ModusError` hierarchy.
- Example scripts live under `sdk/python/examples/` (monorepo only; not
  included in the published wheel or `modus-sdk-python` mirror).

## [0.1.0] — 2026-05-24

Initial release: read APIs for skills and agents, context items CRUD, and
conversations.

### Added
- `APIConnectionError` — typed exception for network-level failures (ConnectError, ReadTimeout, etc.)
- `request_id` attribute on all `ModusError` subclasses — copy the value when filing a support ticket
- `ContextItemDeletion` return type from `context.items.delete()`
- Skills write: `create()`, `update()`, `deploy()`, `delete()`
- Agents write: `create()`, `update()`, `deploy()`, `delete()`
- Context items: `lookup()`, `list_values()`
- Async parity for all new methods on `AsyncModus`
- User-Agent header on every request (`modus-python/0.1.0 (python/3.x; OS)`)
- Split connect/read timeout (5s connect, 300s read by default)
- `MODUS_TIMEOUT` and `MODUS_MAX_RETRIES` environment variable support
- `py.typed` marker — full mypy/pyright support
- OpenAPI drift CI test — catches backend field renames before merge
- Public schema snapshot tests — prevents accidental API surface breaks
- `scripts/run_examples.sh` — local end-to-end validation script

### Changed
- `ModusConfig` is now a frozen dataclass — mutation after construction raises `FrozenInstanceError`
- Default timeout changed from 60s (single) to split: 5s connect + 300s read
- Network-level errors (`ConnectError`, `ReadTimeout`, etc.) are now retried automatically
- `ModusConfig.__repr__` masks the API key to prevent accidental logging

### Fixed
- `httpx.ReadTimeout`, `WriteTimeout`, `PoolTimeout` now correctly raise `APIConnectionError` instead of leaking raw httpx exceptions
- `_http.patch()` no longer crashes with `JSONDecodeError` when backend returns 204
- `context.items.get/update/delete` now correctly URL-encodes the `uid` path parameter
- `build_page()` raises `ModusError` on unexpected response shape instead of silently returning empty

### Breaking Changes
- `context.items.delete()` now returns `ContextItemDeletion` instead of `None`
- `ModusError.__init__` has new optional keyword arguments (`request_id`, `response_headers`, `body`, `code`)
- `client.skills.run()` and `client.skills.stream()` removed from the public surface (no matching `@PublicApi` operation). Use `chat()` / `chat_stream()` since 0.2.0.
- `client.agents.runs.list()` removed from the public surface. The backend endpoint `GET /api/v1/agents/:id/runs` has no `@PublicApi` decorator and rejects PAT tokens.
- Public exports removed from `modus`: `RunCancelledError`, `StreamTimeoutError` (internal in `modus._exceptions`). SSE event types remain in `modus.types.runs`.
- `examples/run_skill_when_ready.py` and `examples/chat_demo/` removed; both demonstrated APIs that are not in the spec. They will be re-added in v0.3 once the run endpoint lands.

### Contract principle
- The SDK now formally exposes a method only when there is a corresponding `@PublicApi` operation in `apps/services/modus-api/openapi/v1.json`. See [docs/COMPATIBILITY.md](docs/COMPATIBILITY.md) for the full change-management policy.
