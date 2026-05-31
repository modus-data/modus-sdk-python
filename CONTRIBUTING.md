# Contributing

Thank you for your interest in the Modus Python SDK.

## Reporting Issues

Please open a [GitHub issue](https://github.com/modus-data/modus-sdk-python/issues)
for bug reports and feature requests. Include:

- SDK version (`python -c "import modus; print(modus.__version__)"`)
- Python version
- A minimal reproducible example

For security vulnerabilities, see [SECURITY.md](SECURITY.md) — do not open
a public issue.

## Questions & Support

For usage questions and general support, use the
[Modus community forum](https://modus.com) or email **support@modus.com**.

## Pull Requests

The SDK source lives in the `modus-data/modus` monorepo. This repository
is a release mirror — pull requests are not accepted here. If you have a
proposed fix or feature, please open an issue and the team will handle it
from the monorepo.

## Development (monorepo)

From the repository root (requires [Node.js](https://nodejs.org/) + [pnpm](https://pnpm.io/) per `.nvmrc`, and [uv](https://docs.astral.sh/uv/) on your `PATH`):

```bash
pnpm sdk:test                  # pytest
pnpm sdk:lint                  # mypy
pnpm sdk:requirements-drift    # regenerate + verify Snyk requirements.txt files
pnpm sdk:build                 # build wheel/sdist locally
```

These run via Nx (`modus-sdk` project). They are not included in root
`pnpm test` / `pnpm build` (Python is excluded via `lang:python` tag).
