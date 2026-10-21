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


@pytest.mark.parametrize("paginated", [False, True])
def test_infers_registered_query_ref_with_python_alias(paginated: bool) -> None:
    hints = (_list_hints if paginated else _hints)(["view"])
    hints["types"] = {**_TYPES, "ProbeView": {
        "ts": "src/types/probes.ts", "py": "modus.types.views", "pyName": "PublicView",
    }}
    parameters = _query_parameters("view", view={"$ref": "#/components/schemas/ViewAlias"})
    spec = _list_spec(parameters) if paginated else _spec("get", parameters)
    spec["components"] = {"schemas": {**_COMPONENTS["schemas"], "ViewAlias": {
        "$ref": "#/components/schemas/ProbeView",
    }}}
    source = emit_resource_files(hints, spec)[0][1]
    assert source.count("view: Optional[PublicView] = None") == 2
    assert "from modus.types.views import PublicView" in source


@pytest.mark.parametrize("scalar", ["str", "bool"])
def test_rejects_query_override_with_a_different_scalar(scalar: str) -> None:
    hints = _hints([{"name": "depth", "ts": "string", "py": scalar}])
    with pytest.raises(ValueError, match="depth.*disagrees with.*spec scalar"):
        emit_resource_files(hints, _spec("get", _query_parameters("depth", depth={"type": "integer"})))


def test_rejects_named_string_schema_overriding_numeric_query() -> None:
    hints = _hints([{"name": "depth", "ts": "ProbeView", "py": "ProbeView"}])
    hints["types"] = {**_TYPES, "ProbeView": {"ts": "src/types/probes.ts", "py": "modus.types.views"}}
    with pytest.raises(ValueError, match="depth.*disagrees with.*spec scalar"):
        emit_resource_files(hints, _spec("get", _query_parameters("depth", depth={"type": "integer"})))


@pytest.mark.parametrize("paginated", [False, True])
def test_authored_python_examples_preserve_sync_code_and_indentation(paginated: bool) -> None:
    hints = (_list_hints if paginated else _hints)([])
    operation = next(iter(hints["operations"].values()))
    operation["exposures"][0]["examples"] = {
        "py": [">>> for row in client.probes.list():\n...     print(row.id)", ">>> print(client.probes)"],
    }
    source = emit_resource_files(hints, _list_spec([]) if paginated else _spec("get", []))[0][1]
    assert source.count("        Example:\n            >>> for row in client.probes.list():\n            ...     print(row.id)") == 1
    assert source.count("        Example:\n            >>> print(client.probes)") == 1


@pytest.mark.parametrize("paginated", [False, True])
def test_doc_operation_references_use_public_names_on_the_same_exposure(paginated: bool) -> None:
    hints = _list_hints(["source"]) if paginated else _hints(["source"])
    hints["operations"]["ProbeController_createSlot"] = {
        "mode": "custom",
        "exposures": [
            {"surface": "management", "resource": ["probes"], "method": "manageSlot"},
            {"surface": "consumption", "resource": ["otherProbes"], "method": "otherSlot"},
            {"surface": "consumption", "resource": ["probes"], "method": "allocateSlot",
             "pyMethod": "reserve_slot"},
        ],
    }
    parameters = _query_parameters("source")
    parameters[0]["description"] = "Source returned by `createSlot`."
    spec = _list_spec(parameters) if paginated else _spec("get", parameters)
    operation = next(iter(spec["paths"].values()))["get"]
    operation["description"] = "Use `createSlot()` to reserve a slot."
    operation["responses"]["200"]["description"] = "Result of `createSlot`."
    source = emit_resource_files(hints, spec)[0][1]
    assert source.count("Use ``reserve_slot()`` to reserve a slot.") == 2
    assert source.count("Source returned by ``reserve_slot``.") == 2
    assert source.count("Result of ``reserve_slot``.") == 2
    assert "create_slot" not in source
    assert "manage_slot" not in source
    assert "other_slot" not in source
    assert "allocate_slot" not in source


@pytest.mark.parametrize("guard", [None, "record"])
def test_python_model_validation_is_independent_of_ts_response_guard(guard) -> None:
    hints = _hints([])
    if guard:
        hints["operations"]["ProbeController_update"]["exposures"][0]["tsResponseGuard"] = guard
    source = emit_resource_files(hints, _spec("get", []))[0][1]
    assert source.count("return Probe.model_validate(raw)") == 2


def test_unwrapped_list_can_preserve_typing_list_annotation() -> None:
    hints = _hints([])
    hints["operations"]["ProbeController_update"]["exposures"][0].update({
        "unwrap": "probes", "pyListType": "List",
    })
    spec = _spec("get", [])
    spec["paths"]["/api/v1/probes/{probeId}"]["get"]["responses"]["200"] = {
        "content": {"application/json": {"schema": {"$ref": "#/components/schemas/ProbeEnvelope"}}}
    }
    spec["components"] = {"schemas": {"ProbeEnvelope": {
        "type": "object", "properties": {"probes": {"type": "array", "items": {"type": "object"}}},
    }}}
    source = dict(emit_resource_files(hints, spec))["_generated/resources/consumption/probes.py"]
    assert "from typing import List" in source
    assert source.count("-> List[Probe]:") == 2


def test_exposure_page_defaults_and_maximums() -> None:
    hints = _list_hints([])
    hints["operations"]["ProbeController_list"]["exposures"][0]["pageSize"] = {
        "default": 50, "max": 200,
    }
    source = dict(emit_resource_files(hints, _list_spec([])))[
        "_generated/resources/consumption/probes.py"
    ]
    assert source.count("page_size: int = 50") == 2
    assert source.count("validate_page_size(page_size, max_page_size=200)") == 2
    assert source.count("Items per page. Defaults to 50.") == 2


def test_factory_validated_bound_ids_keep_positional_validation() -> None:
    hints = _hints([])
    hints["operations"]["ProbeController_update"]["exposures"][0].update({
        "bind": {"probeId": "probeId"},
        "idValidation": {"argumentNames": True, "bound": False},
    })
    spec = _spec("get", [{"name": "childId", "in": "path"}])
    spec["paths"]["/api/v1/probes/{probeId}/children/{childId}"] = spec["paths"].pop(
        "/api/v1/probes/{probeId}"
    )
    source = dict(emit_resource_files(hints, spec))["_generated/resources/consumption/probes.py"]
    assert "validate_id(self._probe_id" not in source
    assert source.count('validate_id(child_id, name="child_id")') == 2
    assert source.count('path_params={"probeId": self._probe_id, "childId": child_id}') == 2

# Component schemas the cases below point ``$ref`` parameter schemas at.
_COMPONENTS = {
    "schemas": {
        "ProbeView": {"type": "string", "enum": ["active", "draft"]},
        "ProbeDepth": {"$ref": "#/components/schemas/ProbeDepthValue"},
        "ProbeDepthValue": {"type": "integer"},
        "ProbeFilter": {"type": "object", "properties": {"owner": {"type": "string"}}},
    }
}


def _spec(method: str, parameters: list[dict]) -> dict:
    return {
        "components": _COMPONENTS,
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


def _query_parameters(
    *names: str, required: tuple[str, ...] = (), **schemas: dict
) -> list[dict]:
    """Query parameters for ``names``; each defaults to an optional plain string schema."""
    return [
        {
            "name": name,
            "in": "query",
            "description": f"The {name}.",
            "required": name in required,
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


def _render(
    query: list[str],
    method: str = "patch",
    required: tuple[str, ...] = (),
    **schemas: dict,
) -> str:
    spec = _spec(method, _query_parameters(*query, required=required, **schemas))
    files = dict(emit_resource_files(_hints(query), spec))
    return files["_generated/resources/consumption/probes.py"]


def _list_spec(parameters: list[dict]) -> dict:
    return {
        "components": _COMPONENTS,
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


def _render_list(
    query: list[str], required: tuple[str, ...] = (), **schemas: dict
) -> str:
    spec = _list_spec(_query_parameters(*query, required=required, **schemas))
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


@pytest.mark.parametrize("paginated", [False, True])
def test_docs_omit_unexposed_query_parameters_from_all_prose(paginated: bool) -> None:
    parameters = _query_parameters("source", "hiddenFilter")
    parameters[0]["description"] = "Choose the source. Cannot combine with `hiddenFilter`."
    spec = _list_spec(parameters) if paginated else _spec("get", parameters)
    operation = next(iter(spec["paths"].values()))["get"]
    operation["description"] = (
        "Returns matching probes. Optional `hiddenFilter` narrows results. "
        "Use `source` to select a surface."
    )
    hints = _list_hints(["source"]) if paginated else _hints(["source"])
    source = next(iter(dict(emit_resource_files(hints, spec)).values()))

    assert "hiddenFilter" not in source
    assert "hidden_filter" not in source
    assert source.count("Returns matching probes.") == 2
    assert source.count("Use ``source`` to select a surface.") == 2
    assert source.count("source: Choose the source.") == 2


@pytest.mark.parametrize("description", [
    "Items per page. Defaults to 10, clamped to 100.",
    "Items per page. Defaults to 100 when no pagination params are sent (legacy); otherwise 25.",
    "",
])
def test_docs_use_sdk_page_size_default(description: str) -> None:
    parameters = _query_parameters("pageSize")
    parameters[0]["description"] = description
    source = next(iter(dict(emit_resource_files(_list_hints([]), _list_spec(parameters))).values()))

    assert source.count("page_size: Items per page. Defaults to 25.") == 2
    assert "Defaults to 10" not in source
    assert "legacy" not in source


def test_docs_preserve_page_prose_when_legacy_page_parameter_is_unexposed() -> None:
    parameters = _query_parameters("page", "pageToken")
    parameters[1]["description"] = "Opaque token. Omit for the first page."
    spec = _list_spec(parameters)
    spec["paths"]["/api/v1/probes"]["get"]["description"] = (
        "Returns a page of probes. The legacy `page` parameter selects a page by number."
    )
    source = next(iter(dict(emit_resource_files(_list_hints([]), spec)).values()))
    assert source.count("Returns a page of probes.") == 2
    assert source.count("page_token: Opaque token. Omit for the first page.") == 2
    assert "legacy ``page``" not in source


def test_a_required_query_parameter_has_no_default_and_seeds_the_query() -> None:
    source = _render(["since", "view"], required=("since",))
    assert "*, since: str, view: Optional[str] = None) -> Probe:" in source
    assert (
        '        query: dict = {"since": since}\n'
        "        if view is not None:\n"
        '            query["view"] = view\n'
    ) in source


def test_only_required_query_parameters_leave_optional_unimported() -> None:
    source = _render(["since", "until"], required=("since", "until"))
    assert "Optional" not in source
    assert '        query: dict = {"since": since, "until": until}\n' in source


def test_a_required_filter_on_a_paginated_method_is_refused() -> None:
    with pytest.raises(ValueError, match='query parameter "since" is required'):
        _render_list(["since"], required=("since",))


def test_a_required_update_mask_still_goes_through_the_query_helper() -> None:
    """``update_mask_query`` owns the non-empty check a seeded query literal would skip."""
    source = _render(["updateMask"], required=("updateMask",))
    assert "update_mask: str" in source
    assert '        query: dict = {}\n' in source
    assert '"updateMask": update_mask' not in source
    assert (
        "        update_mask_params = update_mask_query(update_mask)\n"
        "        if update_mask_params is not None:\n"
        "            query.update(update_mask_params)\n"
    ) in source


def test_a_required_update_mask_beside_a_seeded_required_filter() -> None:
    source = _render(["since", "updateMask"], required=("since", "updateMask"))
    assert '        query: dict = {"since": since}\n' in source
    assert "        update_mask_params = update_mask_query(update_mask)\n" in source


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


def test_a_ref_query_schema_resolves_to_the_scalar_it_names() -> None:
    source = _render(["view"], view={"$ref": "#/components/schemas/ProbeView"})
    assert "view: Optional[str] = None" in source


def test_a_chain_of_refs_is_followed() -> None:
    source = _render_list(["depth"], depth={"$ref": "#/components/schemas/ProbeDepth"})
    assert "depth: Optional[int] = None" in source
    assert "depth: Optional[int]," in source


def test_a_ref_to_an_object_is_refused() -> None:
    with pytest.raises(ValueError, match='ProbeController_list.*query parameter "filter"'):
        _render_list(["filter"], filter={"$ref": "#/components/schemas/ProbeFilter"})


def test_a_ref_no_component_schema_defines_is_refused() -> None:
    with pytest.raises(ValueError, match='query parameter "view".*Absent'):
        _render(["view"], view={"$ref": "#/components/schemas/Absent"})


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
    monkeypatch.setattr(emit_sdk_resources.shutil, "which", lambda _name: "/usr/bin/ruff")

    emit_sdk_resources._format([])

    assert calls == []


def test_a_missing_ruff_fails_with_an_install_hint(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(emit_sdk_resources.shutil, "which", lambda _name: None)

    with pytest.raises(RuntimeError, match="ruff is not on PATH.*uv sync"):
        emit_sdk_resources._format([Path("modus/_generated/resources/consumption/probes.py")])


def test_an_unnamed_type_is_refused() -> None:
    hints = _hints([])
    hints["types"] = {}
    with pytest.raises(ValueError, match='Probe is used by an exposure but absent from "types"'):
        emit_resource_files(hints, _spec("patch", []))


@pytest.mark.parametrize("paginated", [False, True])
def test_declared_query_types_preserve_public_names_and_wire_scalars(paginated: bool) -> None:
    query = [
        {"name": "view", "ts": "ProbeView", "py": "ProbeView"},
        {"name": "managerId", "ts": "number", "py": "int"},
    ]
    hints = (_list_hints if paginated else _hints)(query)
    hints["types"] = {**_TYPES, "ProbeView": {"ts": "src/types/probes.ts", "py": "modus.types.views"}}
    parameters = _query_parameters("view", "managerId", managerId={"type": "number"})
    spec = _list_spec(parameters) if paginated else _spec("patch", parameters)
    source = emit_resource_files(hints, spec)[0][1]
    assert source.count("view: Optional[ProbeView] = None") == 2
    assert source.count("manager_id: Optional[int] = None") == 2
    assert "from modus.types.views import ProbeView" in source
    assert "import int" not in source
    assert '["managerId"] = manager_id' in source


def test_declared_query_types_must_be_named_or_scalar() -> None:
    hints = _hints([{"name": "view", "ts": "str", "py": "ProbeVue"}])
    with pytest.raises(ValueError, match='query parameter "view": declared type "ProbeVue"'):
        emit_resource_files(hints, _spec("patch", _query_parameters("view")))


def test_declared_query_type_does_not_accept_a_non_scalar_wire_value() -> None:
    hints = _hints([{"name": "tags", "ts": "string", "py": "str"}])
    with pytest.raises(ValueError, match='query parameter "tags" is not a scalar'):
        emit_resource_files(hints, _spec("patch", _query_parameters("tags", tags={"type": "array"})))


def test_named_positional_id_preserves_validation_and_wire_name() -> None:
    hints = _hints([])
    hints["operations"]["ProbeController_update"]["exposures"][0]["ids"] = {"probeId": "probeRef"}
    source = emit_resource_files(hints, _spec("patch", []))[0][1]
    assert source.count("probe_ref: Union[int, str]") == 2
    assert source.count('validate_id(probe_ref, name="probe_ref")') == 2
    assert source.count('path_params={"probeId": probe_ref}') == 2


def test_named_id_must_be_an_unbound_path_parameter() -> None:
    hints = _hints([])
    hints["operations"]["ProbeController_update"]["exposures"][0]["ids"] = {"ghost": "probeRef"}
    with pytest.raises(ValueError, match='"ids" names "ghost", which is not a positional path parameter'):
        emit_resource_files(hints, _spec("patch", []))


@pytest.mark.parametrize("paginated", [False, True])
def test_python_type_name_is_used_for_import_annotations_and_parsing(paginated: bool) -> None:
    hints = (_list_hints if paginated else _hints)([])
    hints["types"] = {"Probe": {**_TYPES["Probe"], "pyName": "ProbeRecord"}}
    source = emit_resource_files(hints, _list_spec([]) if paginated else _spec("patch", []))[0][1]
    assert "from modus.types.probes import ProbeRecord" in source
    assert "ProbeRecord.model_validate" in source
    assert "Page[ProbeRecord]" in source if paginated else "-> ProbeRecord:" in source


def test_empty_body_is_sent_without_a_public_argument() -> None:
    hints = _hints([])
    hints["operations"]["ProbeController_update"]["exposures"][0]["emptyBody"] = True
    source = emit_resource_files(hints, _spec("post", []))[0][1]
    assert source.count("json_body={},") == 2
    assert "def update(self, probe_id: str) -> Probe:" in source


def test_empty_and_argument_body_conflict_is_refused() -> None:
    hints = _hints([])
    hints["operations"]["ProbeController_update"]["exposures"][0].update(
        emptyBody=True, body={"arg": "body", "type": "Probe"}
    )
    with pytest.raises(ValueError, match="emptyBody.*body"):
        emit_resource_files(hints, _spec("post", []))


def test_a_resource_with_generated_children_is_an_importable_package() -> None:
    hints = _list_hints([])
    listing = hints["operations"]["ProbeController_list"]
    listing["exposures"].extend([
        {**listing["exposures"][0], "surface": "management"},
        {**listing["exposures"][0], "surface": "management", "resource": ["probes", "records"]},
    ])
    files = emit_resource_files(hints, _list_spec([]))
    sources = dict(files)
    assert len(files) == len(sources)
    assert "_generated/resources/management/probes.py" not in sources
    assert "class _ProbesResourceBase:" in sources["_generated/resources/management/probes/__init__.py"]
    assert "class _AsyncProbesResourceBase:" in sources["_generated/resources/management/probes/__init__.py"]
    assert "class _ProbesRecordsResourceBase:" in sources["_generated/resources/management/probes/records.py"]
    assert "class _ProbesResourceBase:" in sources["_generated/resources/consumption/probes.py"]



def _envelope_spec(field_schema: dict | None = None) -> dict:
    spec = _spec("patch", [])
    spec["components"] = {"schemas": {"Envelope": {"type": "object", "properties": {
        "probes": field_schema or {"type": "array", "items": {"type": "object"}},
    }}}}
    spec["paths"]["/api/v1/probes/{probeId}"]["patch"]["responses"] = {
        "200": {"description": "", "content": {"application/json": {"schema": {
            "$ref": "#/components/schemas/Envelope",
        }}}},
    }
    return spec


def test_unwrap_validates_the_response_envelope_and_returns_its_array() -> None:
    hints = _hints([])
    hints["operations"]["ProbeController_update"]["exposures"][0]["unwrap"] = "probes"
    source = emit_resource_files(hints, _envelope_spec())[0][1]
    assert "from modus._generated.models import Envelope" in source
    assert source.count("-> list[Probe]:") == 2
    assert source.count("return Envelope.model_validate(raw).probes") == 2


@pytest.mark.parametrize("shape", ["missing", "non-array"])
def test_unwrap_refuses_an_invalid_envelope_field(shape: str) -> None:
    hints = _hints([])
    hints["operations"]["ProbeController_update"]["exposures"][0]["unwrap"] = (
        "missing" if shape == "missing" else "probes"
    )
    with pytest.raises(ValueError, match="unwrap.*array"):
        emit_resource_files(hints, _envelope_spec({"type": "string"}) if shape == "non-array" else _envelope_spec())


@pytest.mark.parametrize("by_alias,exclude_none", [(False, True), (True, False)])
def test_body_keeps_python_argument_and_model_dump_options(by_alias: bool, exclude_none: bool) -> None:
    hints = _hints([])
    hints["operations"]["ProbeController_update"]["exposures"][0]["body"] = {
        "arg": "request", "pyArg": "replacement", "type": "Probe",
        "pyDump": {"byAlias": by_alias, "excludeNone": exclude_none},
    }
    source = emit_resource_files(hints, _spec("patch", []))[0][1]
    assert source.count("replacement: Probe") == 2
    assert source.count(f"body = replacement.model_dump(by_alias={by_alias}, exclude_none={exclude_none})") == 2


def test_sync_only_exposure_emits_no_async_base_or_imports() -> None:
    hints = _hints([])
    hints["operations"]["ProbeController_update"]["exposures"][0]["pyAsync"] = False
    source = emit_resource_files(hints, _spec("patch", []))[0][1]
    assert "class _ProbesResourceBase:" in source
    assert "Async" not in source
    assert "async_" not in source


def test_sync_and_async_exposures_cannot_disagree_on_resource_availability() -> None:
    hints = _hints([])
    exposures = hints["operations"]["ProbeController_update"]["exposures"]
    exposures.append({**exposures[0], "method": "replace", "pyAsync": False})
    with pytest.raises(ValueError, match="disagree.*pyAsync"):
        emit_resource_files(hints, _spec("patch", []))


@pytest.mark.parametrize("paginated", [False, True])
def test_operation_binding_preserves_constructor_dispatch(paginated: bool) -> None:
    hints = (_list_hints if paginated else _hints)([])
    operation = next(iter(hints["operations"].values()))
    operation["exposures"][0]["pyOperation"] = "selected_operation"
    source = emit_resource_files(hints, _list_spec([]) if paginated else _spec("patch", []))[0][1]
    assert "class _Operations(Protocol):" in source
    assert "def selected_operation(self) -> str:" in source
    assert source.count("ops: _Operations") == 2
    assert source.count("self._ops = ops") == 2
    assert source.count("self._ops.selected_operation,") == 2


def test_bound_id_validation_can_precede_positional_path_arguments() -> None:
    hints = _hints([])
    hints["operations"]["ProbeController_update"]["exposures"][0].update(
        bind={"parentId": "scopeId"}, boundIdsFirst=True,
    )
    spec = _spec("patch", [{"name": "parentId", "in": "path"}])
    spec["paths"] = {"/api/v1/parents/{parentId}/probes/{probeId}": next(iter(spec["paths"].values()))}
    source = emit_resource_files(hints, spec)[0][1]
    for cls in source.split("class ")[1:]:
        assert cls.index('validate_id(self._scope_id, name="scope_id")') < cls.index(
            'validate_id(probe_id, name="probe_id")'
        )
