"""
Guards for sdk/python/dev-examples/ — scripts referenced by run_all.sh exist and
follow consumption vs management patterns after DTO re-export alignment.
"""
from __future__ import annotations

import ast
import re
from pathlib import Path

import pytest

_EXAMPLES_DIR = Path(__file__).resolve().parents[3] / "dev-examples"
_RUN_ALL = _EXAMPLES_DIR / "run_all.sh"


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
    # Underscore modules (e.g. _display.py) are shared helpers, not runnable examples.
    on_disk = {
        p.name for p in _EXAMPLES_DIR.glob("*.py") if not p.name.startswith("_")
    }
    listed = set(all_run_all_scripts)
    unlisted = sorted(on_disk - listed)
    assert not unlisted, (
        f"Add these examples to ALL_EXAMPLES in run_all.sh: {unlisted}"
    )


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


def test_list_skills_uses_management_for_detail() -> None:
    path = _EXAMPLES_DIR / "list_skills.py"
    if not path.exists():
        pytest.skip("list_skills.py not present")
    assert _imports_modus_management(path)
    assert _has_attr_chain(path, ("mgmt", "skills", "get"))
    assert _has_attr_chain(path, ("client", "skills", "get"))


def test_list_agents_uses_both_clients_for_detail() -> None:
    path = _EXAMPLES_DIR / "list_agents.py"
    if not path.exists():
        pytest.skip("list_agents.py not present")
    assert _imports_modus_management(path)
    assert _has_attr_chain(path, ("mgmt", "agents", "get"))
    assert _has_attr_chain(path, ("client", "agents", "get"))


def test_context_lookup_demo_covers_lookup_and_values() -> None:
    path = _EXAMPLES_DIR / "context_lookup_demo.py"
    if not path.exists():
        pytest.skip("context_lookup_demo.py not present")
    assert _has_attr_chain(path, ("client", "context", "items", "lookup"))
    assert _has_attr_chain(path, ("client", "context", "items", "list_values"))


_BANNED_DISPLAY_IMPORTS = frozenset(
    {
        "context_content_title",
        "context_item_label",
        "context_item_verified_suffix",
        "note_body",
        "note_content_for_update",
    }
)


def _display_imports(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(), filename=str(path))
    found: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module == "_display":
            for alias in node.names:
                found.add(alias.name)
    return found


def test_dev_examples_do_not_import_context_field_helpers_from_display() -> None:
    offenders: list[str] = []
    for path in sorted(_EXAMPLES_DIR.glob("*.py")):
        if path.name.startswith("_"):
            continue
        banned = _display_imports(path) & _BANNED_DISPLAY_IMPORTS
        if banned:
            offenders.append(f"{path.name}: {sorted(banned)}")
    assert not offenders, f"Use modus.* context accessors instead: {offenders}"


def test_consumption_get_can_use_variation_when_present() -> None:
    """Consumption Skill is a full DTO — examples may read skill.variation on get()."""
    path = _EXAMPLES_DIR / "list_skills.py"
    if not path.exists():
        pytest.skip("list_skills.py not present")
    tree = ast.parse(path.read_text(), filename=str(path))
    chains = {
        _attr_chain(node)
        for node in ast.walk(tree)
        if isinstance(node, ast.Attribute)
    }
    assert ("skill", "variation") in chains or ("skill", "access_config") in chains
