"""
Guards for sdk/python/dev-examples/ — scripts referenced by run_all.sh exist and
avoid consumption Skill/Agent fields that belong on ModusManagement only.
"""
from __future__ import annotations

import ast
import re
from pathlib import Path

import pytest

_EXAMPLES_DIR = Path(__file__).resolve().parents[3] / "dev-examples"
_RUN_ALL = _EXAMPLES_DIR / "run_all.sh"

# Fields on modus.types.skills.Skill / agents.Agent (consumption), not management.
_FORBIDDEN_CONSUMPTION_ATTRS = frozenset(
    {
        "variation",
        "access_config",
        "created_at",
        "updated_at",
        "model",
        "toolset",
        "connection_set",
    }
)


def _scripts_from_run_all_array(name: str) -> list[str]:
    text = _RUN_ALL.read_text()
    pattern = rf"{name}=\(\s*(.*?)\s*\)"
    match = re.search(pattern, text, re.DOTALL)
    assert match, f"run_all.sh must define {name}=(...)"
    block = match.group(1)
    return re.findall(r"[\w_]+\.py", block)


@pytest.fixture(scope="module")
def all_run_all_scripts() -> list[str]:
    if not _RUN_ALL.exists():
        pytest.skip("dev-examples/run_all.sh not found (monorepo layout)")
    return _scripts_from_run_all_array("ALL_EXAMPLES")


def test_all_run_all_scripts_exist(all_run_all_scripts: list[str]) -> None:
    missing = [name for name in all_run_all_scripts if not (_EXAMPLES_DIR / name).exists()]
    assert not missing, f"ALL_EXAMPLES references missing scripts: {missing}"


def test_example_py_files_listed_in_run_all(all_run_all_scripts: list[str]) -> None:
    on_disk = {p.name for p in _EXAMPLES_DIR.glob("*.py")}
    listed = set(all_run_all_scripts)
    unlisted = sorted(on_disk - listed)
    assert not unlisted, (
        f"Add these examples to ALL_EXAMPLES in run_all.sh: {unlisted}"
    )


def _forbidden_attr_accesses(path: Path) -> list[str]:
    tree = ast.parse(path.read_text(), filename=str(path))
    hits: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Attribute) and isinstance(node.attr, str):
            if node.attr in _FORBIDDEN_CONSUMPTION_ATTRS:
                hits.append(f"{path.name}:{node.lineno}: .{node.attr}")
    return hits


def _attr_chain(node: ast.AST) -> tuple[str, ...] | None:
    parts: list[str] = []
    cur: ast.AST | None = node
    while isinstance(cur, ast.Attribute):
        parts.append(cur.attr)
        cur = cur.value
    if isinstance(cur, ast.Name):
        parts.append(cur.id)
        return tuple(reversed(parts))
    return None


def _has_attr_chain(path: Path, chain: tuple[str, ...]) -> bool:
    tree = ast.parse(path.read_text(), filename=str(path))
    for node in ast.walk(tree):
        if isinstance(node, ast.Attribute) and _attr_chain(node) == chain:
            return True
    return False


def _imports_modus_management(path: Path) -> bool:
    tree = ast.parse(path.read_text(), filename=str(path))
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module == "modus.management":
            for alias in node.names:
                if alias.name == "ModusManagement":
                    return True
    return False


def _uses_name_attr(path: Path, var_name: str, attr: str) -> bool:
    tree = ast.parse(path.read_text(), filename=str(path))
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.Attribute)
            and node.attr == attr
            and isinstance(node.value, ast.Name)
            and node.value.id == var_name
        ):
            return True
    return False


@pytest.mark.parametrize(
    "script",
    [
        "org_overview.py",
        "sync_knowledge.py",
        "list_context.py",
        "manage_context.py",
        "context_lookup_demo.py",
    ],
)
def test_consumption_examples_avoid_management_only_skill_fields(script: str) -> None:
    path = _EXAMPLES_DIR / script
    if not path.exists():
        pytest.skip(f"{script} not present")
    hits = _forbidden_attr_accesses(path)
    assert not hits, (
        f"{script} accesses fields not on consumption Skill/Agent. "
        f"Use ModusManagement for detail. Found: {hits}"
    )


def test_list_skills_uses_management_for_detail() -> None:
    path = _EXAMPLES_DIR / "list_skills.py"
    if not path.exists():
        pytest.skip("list_skills.py not present")
    assert _imports_modus_management(path)
    assert _has_attr_chain(path, ("mgmt", "skills", "get"))
    assert _has_attr_chain(path, ("client", "skills", "get"))


def test_list_agents_uses_management_for_timestamps() -> None:
    path = _EXAMPLES_DIR / "list_agents.py"
    if not path.exists():
        pytest.skip("list_agents.py not present")
    assert _imports_modus_management(path)
    assert _has_attr_chain(path, ("mgmt", "agents", "get"))
    assert _has_attr_chain(path, ("client", "agents", "get"))
    assert not _uses_name_attr(path, "agent", "created_at")


def test_context_lookup_demo_covers_lookup_and_values() -> None:
    path = _EXAMPLES_DIR / "context_lookup_demo.py"
    if not path.exists():
        pytest.skip("context_lookup_demo.py not present")
    assert _has_attr_chain(path, ("client", "context", "items", "lookup"))
    assert _has_attr_chain(path, ("client", "context", "items", "list_values"))
