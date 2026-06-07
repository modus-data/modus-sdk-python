# Changelog

**Current release:** `0.1.5` on [TestPyPI](https://test.pypi.org/project/modus-sdk/).

## [Unreleased]

### Changed

- **Breaking:** `client.skills.get_context()` returns `SkillContextComposition.context` (composed markdown string) instead of `context_items`. `limit` applies only when the API falls back to structured JSON.

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
