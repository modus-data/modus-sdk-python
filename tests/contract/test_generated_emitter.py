"""The resource emitter's query templates, on shapes no real operation uses yet.

The pilot operations cover a single ordinary filter and a lone ``updateMask``. These cases
render from an in-memory hints + spec pair so the general templates — several ordinary
filters, and ordinary filters mixed with ``updateMask`` — are pinned before an operation
needs them, together with the guards that refuse a shape the templates cannot express.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

SCRIPTS_DIR = Path(__file__).resolve().parents[3] / "scripts"

sys.path.insert(0, str(SCRIPTS_DIR))
import emit_sdk_resources  # noqa: E402
from emit_sdk_resources import emit_resource_files  # noqa: E402

_TYPES = {"Probe": {"ts": "src/types/probes.ts", "py": "modus.types.probes"}}


def _spec(method: str, parameters: list[dict]) -> dict:
    return {
        "paths": {
            "/api/v1/probes/{probeId}": {
                method: {
                    "operationId": "ProbeController_update",
                    "x-modus-service": "modus-api",
                    "summary": "Update a probe",
                    "parameters": [
                        {"name": "probeId", "in": "path", "description": "Probe id."},
                        *parameters,
                    ],
                    "responses": {"200": {"description": ""}},
                }
            }
        }
    }


def _query_parameters(*names: str, **schemas: dict) -> list[dict]:
    """Query parameters for ``names``; each defaults to a plain string schema."""
    return [
        {
            "name": name,
            "in": "query",
            "description": f"The {name}.",
            "schema": schemas.get(name, {"type": "string"}),
        }
        for name in names
    ]


def _hints(query: list[str]) -> dict:
    return {
        "types": _TYPES,
        "operations": {
            "ProbeController_update": {
                "mode": "generated",
                "exposures": [
                    {
                        "surface": "consumption",
                        "resource": ["probes"],
                        "method": "update",
                        "query": query,
                        "returns": "Probe",
                    }
                ],
            }
        },
    }


def _render(query: list[str], method: str = "patch", **schemas: dict) -> str:
    spec = _spec(method, _query_parameters(*query, **schemas))
    files = dict(emit_resource_files(_hints(query), spec))
    return files["_generated/resources/consumption/probes.py"]


def _list_spec(parameters: list[dict]) -> dict:
    return {
        "paths": {
            "/api/v1/probes": {
                "get": {
                    "operationId": "ProbeController_list",
                    "x-modus-service": "modus-api",
                    "summary": "List probes",
                    "parameters": parameters,
                    "responses": {"200": {"description": ""}},
                }
            }
        }
    }


def _list_hints(query: list[str]) -> dict:
    return {
        "types": _TYPES,
        "operations": {
            "ProbeController_list": {
                "mode": "generated",
                "exposures": [
                    {
                        "surface": "consumption",
                        "resource": ["probes"],
                        "method": "list",
                        "query": query,
                        "returns": "Probe",
                    }
                ],
                "pagination": {"items": "probes"},
            }
        },
    }


def _render_list(query: list[str], **schemas: dict) -> str:
    spec = _list_spec(_query_parameters(*query, **schemas))
    files = dict(emit_resource_files(_list_hints(query), spec))
    return files["_generated/resources/consumption/probes.py"]


def test_ordinary_filters_are_keyword_only_and_omitted_when_none() -> None:
    source = _render(["search", "ownerId"])
    assert "*,\n        search: Optional[str] = None,\n        owner_id: Optional[str] = None," in (
        source
    )
    assert (
        "        query: dict = {}\n"
        '        if search is not None:\n'
        '            query["search"] = search\n'
        "        if owner_id is not None:\n"
        '            query["ownerId"] = owner_id\n'
    ) in source


def test_update_mask_goes_through_the_query_helper() -> None:
    source = _render(["updateMask"])
    assert "from modus._query import update_mask_query" in source
    assert (
        "        query: dict = {}\n"
        "        update_mask_params = update_mask_query(update_mask)\n"
        "        if update_mask_params is not None:\n"
        "            query.update(update_mask_params)\n"
    ) in source


def test_a_mixed_query_combines_both() -> None:
    source = _render(["search", "updateMask"])
    assert (
        "        query: dict = {}\n"
        "        if search is not None:\n"
        '            query["search"] = search\n'
        "        update_mask_params = update_mask_query(update_mask)\n"
        "        if update_mask_params is not None:\n"
        "            query.update(update_mask_params)\n"
    ) in source


def test_docstrings_name_wire_identifiers_the_python_way() -> None:
    spec = _spec("patch", [])
    operation = spec["paths"]["/api/v1/probes/{probeId}"]["patch"]
    operation["description"] = "Pass `nextPageToken`, see `MemorySearchRequest` and `scopes:read`."
    source = emit_resource_files(_hints([]), spec)[0][1]
    # camelCase wire names become the snake_case argument; other literals are left alone.
    assert "Pass ``next_page_token``, see ``MemorySearchRequest`` and ``scopes:read``." in source


def test_query_argument_types_come_from_the_spec_schema() -> None:
    source = _render(
        ["managerId", "archived"],
        managerId={"type": "integer"},
        archived={"type": "boolean"},
    )
    assert "manager_id: Optional[int] = None" in source
    assert "archived: Optional[bool] = None" in source


def test_a_paginated_filter_is_typed_from_the_spec_schema() -> None:
    source = _render_list(["managerId"], managerId={"type": "integer"})
    assert "manager_id: Optional[int] = None" in source
    assert "manager_id: Optional[int]," in source


def test_a_string_enum_stays_a_string() -> None:
    source = _render(["state"], state={"type": "string", "enum": ["live", "draft"]})
    assert "state: Optional[str] = None" in source


def test_a_non_scalar_query_parameter_is_refused() -> None:
    with pytest.raises(ValueError, match='ProbeController_list.*query parameter "tags"'):
        _render_list(["tags"], tags={"type": "array", "items": {}})


def test_a_query_parameter_absent_from_the_spec_is_refused() -> None:
    with pytest.raises(ValueError, match='query parameter "ghost"'):
        emit_resource_files(_hints(["ghost"]), _spec("patch", []))


def test_query_parameters_are_refused_where_the_request_would_drop_them() -> None:
    # invoke_operation forwards `query` for GET, PATCH and PUT only.
    with pytest.raises(ValueError, match="POST requests cannot carry query parameters"):
        _render(["search"], method="post")


def test_nothing_emitted_runs_no_formatter(monkeypatch: pytest.MonkeyPatch) -> None:
    """``ruff format`` / ``ruff check --fix`` with no operand would rewrite the whole tree."""
    calls = []
    monkeypatch.setattr(emit_sdk_resources.subprocess, "run", lambda *a, **k: calls.append(a))

    emit_sdk_resources._format([])

    assert calls == []


def test_an_unnamed_type_is_refused() -> None:
    hints = _hints([])
    hints["types"] = {}
    with pytest.raises(ValueError, match='Probe is used by an exposure but absent from "types"'):
        emit_resource_files(hints, _spec("patch", []))
