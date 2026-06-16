# Changelog

**Current TestPyPI release:** [`0.1.6`](https://test.pypi.org/project/modus-sdk/) (2026-06-15). Production PyPI not yet published.

## [Unreleased]

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
