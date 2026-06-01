"""
OpenAPI list-operation drift guard.

Ensures AIP-158 list resources only send query params allowed by openapi/v1.json
and never send non-AIP ``limit`` / ``cursor``.
Monorepo-only — skipped outside the monorepo (same as test_openapi_drift.py).
"""
from __future__ import annotations

import inspect
import json
from pathlib import Path
from typing import Any, Callable, Dict, Set

import pytest
from modus._pagination import aip_list_params
from modus.resources.context.items import _context_list_params

_OPENAPI_PATH = Path(__file__).parents[4] / "apps/services/modus-api/openapi/v1.json"

pytestmark = pytest.mark.skipif(
    not _OPENAPI_PATH.exists(),
    reason="openapi/v1.json not found — drift test only runs inside the monorepo",
)

_FORBIDDEN_LIST_PARAMS = frozenset({"limit", "cursor"})


@pytest.fixture(scope="module")
def openapi() -> dict:
    return json.loads(_OPENAPI_PATH.read_text())


def _allowed_query_params(openapi: dict, operation_id: str) -> Set[str]:
    for path_item in openapi.get("paths", {}).values():
        for method, op in path_item.items():
            if method not in ("get", "post", "put", "patch", "delete"):
                continue
            if not isinstance(op, dict) or op.get("operationId") != operation_id:
                continue
            names: Set[str] = set()
            for param in op.get("parameters", []):
                if param.get("in") == "query" and "name" in param:
                    names.add(param["name"])
            return names
    raise KeyError(f"operationId {operation_id!r} not found in OpenAPI spec")


def _assert_aip_params_subset(
    params: Dict[str, Any],
    *,
    operation_id: str,
    openapi: dict,
) -> None:
    allowed = _allowed_query_params(openapi, operation_id)
    actual = set(params.keys())
    assert actual <= allowed, (
        f"{operation_id}: SDK params {sorted(actual)} not subset of OpenAPI "
        f"query params {sorted(allowed)}"
    )
    assert not (actual & _FORBIDDEN_LIST_PARAMS), (
        f"{operation_id}: non-AIP pagination params {sorted(actual & _FORBIDDEN_LIST_PARAMS)}"
    )
    assert "pageSize" in actual, f"{operation_id}: missing required pageSize"


@pytest.mark.parametrize(
    "operation_id,build_params",
    [
        (
            "SkillsController_list",
            lambda: aip_list_params(25, None),
        ),
        (
            "AgentsController_list",
            lambda: aip_list_params(25, "tok_abc"),
        ),
        (
            "ContextItemsController_list",
            lambda: _context_list_params(25, None, None),
        ),
        (
            "ContextItemsController_list",
            lambda: _context_list_params(25, "tok_abc", "metric"),
        ),
        (
            "ContextItemsController_listValues",
            lambda: aip_list_params(
                25,
                None,
                contextType="salesforce_object_field",
                contentKeyPath="enumValues",
            ),
        ),
    ],
)
def test_list_operations_use_openapi_query_params(
    openapi: dict,
    operation_id: str,
    build_params: Callable[[], Dict[str, Any]],
) -> None:
    _assert_aip_params_subset(build_params(), operation_id=operation_id, openapi=openapi)


def test_skills_list_page_builds_aip_params() -> None:
    from modus.resources.skills.skills import SkillsResource

    source = inspect.getsource(SkillsResource._list_page)
    assert "aip_list_params" in source


def test_agents_list_page_builds_aip_params() -> None:
    from modus.resources.agents.agents import AgentsResource

    source = inspect.getsource(AgentsResource._list_page)
    assert "aip_list_params" in source


@pytest.mark.parametrize(
    "module_path,class_name",
    [
        ("modus.management.resources.skills.skills", "SkillsResource"),
        ("modus.management.resources.agents.agents", "AgentsResource"),
        ("modus.management.resources.context.items", "ContextItemsResource"),
    ],
)
def test_management_list_pages_use_aip_helpers(module_path: str, class_name: str) -> None:
    import importlib

    mod = importlib.import_module(module_path)
    cls = getattr(mod, class_name)
    source = inspect.getsource(cls._list_page)
    assert "aip_list_params" in source or "_context_list_params" in source
