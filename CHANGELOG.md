# Changelog

[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) · [SemVer](https://semver.org/)

**Current release:** `0.1.2` on [TestPyPI](https://test.pypi.org/project/modus-sdk/) (`sdk-python/v0.1.2`). Production PyPI not published yet.

## [Unreleased]

Planned next release: **`0.1.3`** (tag `sdk-python/v0.1.3`).

### Added

- `modus.Modus` — chat/streaming, context compose, agent runs (on top of read APIs in `0.1.2`).
- `modus.management.ModusManagement` — full configure surface in the same package.

### Changed

- List pagination: `page_size`, `page_token`, `Page.next_page_token`.
- README and public docstrings for package consumers.

## [0.1.2] — 2026-05-28

TestPyPI. Single package: `modus` + `modus.management` (replaces separate management package).

## [0.1.0] — 2026-05-24

TestPyPI. Initial read APIs and management CRUD.
