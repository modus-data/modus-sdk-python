"""
L3: Public schema snapshot test.
Compares current model schemas to committed snapshots.
Failures mean the public API surface changed — update snapshots intentionally.
"""
import json
import pytest
from pathlib import Path

SNAPSHOT_DIR = Path(__file__).parent / "snapshots"


def _load_snapshot(name: str) -> dict:
    path = SNAPSHOT_DIR / f"{name}_schema.json"
    if not path.exists():
        pytest.fail(f"Snapshot missing: {path}. Run: python scripts/update_snapshots.py")
    return json.loads(path.read_text())


def test_skill_schema_stable():
    from modus.types.skills import Skill
    current = Skill.model_json_schema()
    snapshot = _load_snapshot("skill")
    assert current == snapshot, (
        "Skill public schema changed. If intentional:\n"
        "  python scripts/update_snapshots.py\n"
        "  git add tests/snapshots/skill_schema.json\n"
        "  Add a CHANGELOG.md entry"
    )


def test_agent_schema_stable():
    from modus.types.agents import Agent
    current = Agent.model_json_schema()
    snapshot = _load_snapshot("agent")
    assert current == snapshot


def test_context_item_schema_stable():
    from modus.types.context import ContextItem
    current = ContextItem.model_json_schema()
    snapshot = _load_snapshot("context_item")
    assert current == snapshot
