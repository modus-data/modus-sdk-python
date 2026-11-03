"""
L3: Public schema snapshot test.
Compares current model schemas to committed snapshots.
Failures mean the public API surface changed — update snapshots intentionally.
"""
import json
from pathlib import Path

import pytest

SNAPSHOT_DIR = Path(__file__).parent / "snapshots"


def _load_snapshot(name: str) -> dict:
    path = SNAPSHOT_DIR / f"{name}_schema.json"
    if not path.exists():
        pytest.fail(f"Snapshot missing: {path}. Write <model>.model_json_schema() to it, json.dumps(..., indent=2) plus a trailing newline.")
    return json.loads(path.read_text())


def test_scope_schema_stable():
    from modus.types.scopes import Scope
    current = Scope.model_json_schema()
    snapshot = _load_snapshot("skill")
    assert current == snapshot, (
        "Scope public schema changed. If intentional, rewrite the snapshot from the model:\n"
        "  cd distribution/clients/python/modus-sdk\n"
        "  python -c 'import json,pathlib; from modus.types.scopes import Scope; "
        "pathlib.Path(\"tests/snapshots/skill_schema.json\").write_text(json.dumps("
        "Scope.model_json_schema(), indent=2) + chr(10))'\n"
        "  git add tests/snapshots/skill_schema.json\n"
        "  Add a CHANGELOG.md entry"
    )


def test_workflow_schema_stable():
    from modus.types.workflows import Workflow
    current = Workflow.model_json_schema()
    snapshot = _load_snapshot("agent")
    assert current == snapshot


def test_context_item_schema_stable():
    from modus.types.context import ContextItem
    current = ContextItem.model_json_schema()
    snapshot = _load_snapshot("context_item")
    assert current == snapshot
