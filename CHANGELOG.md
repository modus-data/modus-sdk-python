# Changelog

**Current TestPyPI release:** [`0.1.5`](https://test.pypi.org/project/modus-sdk/) (2026-06-04). Production PyPI not yet published.

## [Unreleased]

### Added

- Full **Modus** and **ModusManagement** API coverage (sync + async): skills, agents, chat, context, runs, connections, usage metrics, org admin.
- Context update helpers and read accessors; `Toolset` builders; list filters (`search`, `view`, `type`, `manager_id`); `guardrails=` on skill/agent writes.

### Changed

- Read types match API responses (`Skill`, `Agent`, `ContextItem`, …); early TestPyPI callers may need small updates (e.g. `skill.variation.instructions`, scoped `conversations(skill_id)`, `get_context().context`).
- Typed builders required for toolset, trigger, and agent selection.
- Usage metrics: `model` optional when grouped by skill, agent, or interface (use `group_value`). **Compatibility:** corrects 0.1.5 where `model` was incorrectly required on all breakdowns.

### Fixed

- Context updates, `update_mask` clearing, agent selection payloads, and input validation.

### Removed

- Preview/stub operations; `access_config=` on writes (use `guardrails=`); legacy `Toolset(tools=[...])`.

## [0.1.5] — 2026-06-04

- Product-focused README and examples (`quickstart.py`, `chat.py`, `manage_skill.py`); Streamlit demo branding.

## Prior releases

| Version | Summary |
|---------|---------|
| 0.1.0–0.1.4 | Initial TestPyPI builds: consumption + management clients, examples, trigger fix, ownership transfer fields, README badges. |
