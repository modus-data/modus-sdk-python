# Changelog

[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) · [SemVer](https://semver.org/)

**Current release:** `0.1.3` on [TestPyPI](https://test.pypi.org/project/modus-sdk/) (`sdk-python/v0.1.3`). Production PyPI not published yet.

## [Unreleased]

### Changed

- **Breaking:** `client.skills.get_context()` returns `SkillContextComposition.context` (composed markdown string) instead of `context_items`. `limit` applies only when the API falls back to structured JSON.

## [0.1.4] — 2026-06-01

TestPyPI (`sdk-python/v0.1.4`).

### Fixed

- `mgmt.agents.create()` / `update()`: typed triggers (`AgentTrigger.manual()`, `AgentTrigger.schedule_*()`, etc.) now serialize with snake_case keys (`trigger_type`, `schedule.time_of_day`, ...) to match the agents API, which previously rejected the camelCase payload. The `trigger={"trigger_type": ...}` dict workaround is no longer needed.

### Changed

- README: relative logo path (private `modus-sdk-python` mirror), TestPyPI badges and install instructions.

## [0.1.3] — 2026-06-01

TestPyPI (`sdk-python/v0.1.3`).

### Added

- `modus.Modus` — chat, streaming, context compose, agent runs (on top of read APIs in `0.1.2`).
- `modus.management.ModusManagement` — full configure surface in the same package.
- `mgmt.skills.memories(skill_id)` — list, search, update, delete skill memories.
- Exported types: `AgentTrigger`, `Toolset`, `AgentSelection`, `WorkflowGraph`,
  `Memory`, `MemorySearchRequest`, `MemoryUpdate`, `JsonObject`, and related helpers.

### Changed

- Management `create`/`update` accept typed models for triggers, toolsets, agent
  selection, workflow graphs, and access config (`AgentTrigger.schedule_daily(...)`,
  `Toolset.from_tools(...)`, etc.). Raw dicts still work with `DeprecationWarning`.
- `context.items.list_values` returns `Page[ContextValueRow]`; `Message.tool_calls` is
  `List[ToolCall]`; `SkillContextComposition.context_items` is typed.
- `mgmt.context.items.update` uses explicit keyword fields only (no `**kwargs`).
- List pagination: `page_size`, `page_token`, `Page.next_page_token`.
- README and public docstrings oriented for package consumers (Modus behavior, not internal stack names).

## [0.1.2] — 2026-05-28

TestPyPI. Single package: `modus` + `modus.management` (replaces separate management package).

## [0.1.0] — 2026-05-24

TestPyPI. Initial read APIs and management CRUD.
