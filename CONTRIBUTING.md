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

This repository is a **release mirror** of the Python SDK package. Pull requests
are not accepted here.

Development happens in the Modus monorepo. If you have a proposed fix or feature,
open an issue in this repository and the team will route it internally.

## Running tests (from a source checkout)

If you have cloned this mirror with the `tests/` directory:

```bash
cd modus-sdk   # repository root after mirror split
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
pytest tests/ -m "not integration"
```

Optional live API smoke tests (require a valid token and reachable API):

```bash
export MODUS_API_KEY=modus_xxx
pytest tests/integration/ -m integration
```
