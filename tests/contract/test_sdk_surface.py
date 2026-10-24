"""``distribution/clients/sdk-surface.json`` is the single source of truth for what the SDKs expose.

Every OpenAPI operation needs an entry, every entry must validate against
``sdk-surface.schema.json``, and every exposure must resolve to a real method on both the
sync and the async client.
"""

from __future__ import annotations

import copy
import importlib
import json
import re
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional, Set, Tuple

from modus import AsyncModus, Modus
from modus.management import AsyncModusManagement, ModusManagement

_CLIENTS_DIR = Path(__file__).resolve().parents[4]
_SURFACE = json.loads((_CLIENTS_DIR / "sdk-surface.json").read_text())
_SCHEMA = json.loads((_CLIENTS_DIR / "sdk-surface.schema.json").read_text())

_HTTP_METHODS = {"get", "post", "put", "patch", "delete"}

# ``AsyncScopesResource`` has no ``evaluations()`` factory and the SDK has no
# ``AsyncScopeEvaluationsResource`` at all, so these five operations are sync-only in Python.
# A real gap in the async client, not a wrong hint: the hints rows stay correct. Listed by
# operationId, not by resource, so a new operation on that resource is still caught, and
# ``test_async_gaps_are_still_gaps`` fails the moment the async resource lands — delete the
# entry then.
_ASYNC_GAPS = {
    "EvaluationsController_getConfig",
    "EvaluationsController_updateConfig",
    "EvaluationsController_triggerRun",
    "EvaluationsController_listRuns",
    "EvaluationsController_getRun",
}


def _snake(name: str) -> str:
    return re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", name).lower()


def _deref(ref: str) -> dict:
    node: Any = _SCHEMA
    for part in ref.lstrip("#/").split("/"):
        node = node[part]
    return node


def _schema_errors(node: dict, value: Any, path: str) -> List[str]:
    """Validate the keyword subset the schema uses (no JSON-Schema validator is installed)."""
    if "$ref" in node:
        return _schema_errors(_deref(node["$ref"]), value, path)
    if "oneOf" in node:
        branches = [_schema_errors(sub, value, path) for sub in node["oneOf"]]
        matched = [errors for errors in branches if not errors]
        if len(matched) == 1:
            return []
        if len(matched) > 1:
            return [f"{path}: matched {len(matched)} oneOf branches, expected 1"]
        return [f"{path}: matched no oneOf branch", *[e for branch in branches for e in branch]]

    errors: List[str] = []
    if node.get("type") == "object":
        if not isinstance(value, dict):
            return [f"{path}: expected an object"]
        properties = node.get("properties", {})
        for key in node.get("required", []):
            if key not in value:
                errors.append(f'{path}: missing required property "{key}"')
        minimum = node.get("minProperties")
        if minimum is not None and len(value) < minimum:
            errors.append(f"{path}: expected at least {minimum} properties")
        extra = node.get("additionalProperties")
        for key, child in value.items():
            if key in properties:
                errors.extend(_schema_errors(properties[key], child, f"{path}.{key}"))
            elif extra is False:
                errors.append(f'{path}: unknown property "{key}"')
            elif extra:
                errors.extend(_schema_errors(extra, child, f"{path}.{key}"))
        return errors
    if node.get("type") == "array":
        if not isinstance(value, list):
            return [f"{path}: expected an array"]
        minimum = node.get("minItems")
        if minimum is not None and len(value) < minimum:
            errors.append(f"{path}: expected at least {minimum} items")
        for index, item in enumerate(value):
            errors.extend(_schema_errors(node["items"], item, f"{path}[{index}]"))
        return errors
    if node.get("type") == "string" and not isinstance(value, str):
        return [f"{path}: expected a string"]
    if "enum" in node and value not in node["enum"]:
        errors.append(f"{path}: {value!r} is not one of {node['enum']}")
    if "pattern" in node and isinstance(value, str) and not re.search(node["pattern"], value):
        errors.append(f"{path}: {value!r} does not match {node['pattern']}")
    return errors


def _spec_operation_ids(openapi: dict) -> Set[str]:
    return {
        op["operationId"]
        for path_item in openapi.get("paths", {}).values()
        for method, op in path_item.items()
        if method in _HTTP_METHODS and isinstance(op, dict) and op.get("operationId")
    }


def _exposures() -> Iterator[Tuple[str, dict]]:
    for operation_id, operation in _SURFACE["operations"].items():
        for exposure in operation.get("exposures", []):
            yield operation_id, exposure


def test_every_spec_operation_has_an_entry(openapi: dict) -> None:
    missing = sorted(_spec_operation_ids(openapi) - set(_SURFACE["operations"]))
    assert not missing, f"Operations with no sdk-surface.json entry: {missing}"


def test_no_stale_entries(openapi: dict) -> None:
    stale = sorted(set(_SURFACE["operations"]) - _spec_operation_ids(openapi))
    assert not stale, f"sdk-surface.json entries not in the spec: {stale}"


def test_validates_against_the_schema() -> None:
    assert _schema_errors(_SCHEMA, _SURFACE, "$") == []


# A negative test built on an already-invalid row would pass even with unknown-property
# rejection switched off, so each one starts from a copy of a real row and changes one thing.
def _probe_row() -> dict:
    real = next(op for op in _SURFACE["operations"].values() if op.get("exposures"))
    return copy.deepcopy(real)


def _errors_with_probe(row: dict) -> str:
    probed = {**_SURFACE, "operations": {**_SURFACE["operations"], "ProbeController_probe": row}}
    return "\n".join(_schema_errors(_SCHEMA, probed, "$"))


def test_schema_accepts_the_unmodified_probe_row() -> None:
    assert _errors_with_probe(_probe_row()) == ""


def test_schema_rejects_an_unknown_property_on_an_operation() -> None:
    row = _probe_row()
    row["clii"] = "scopes memories update"
    assert 'unknown property "clii"' in _errors_with_probe(row)


def test_schema_rejects_an_unknown_property_on_an_exposure() -> None:
    row = _probe_row()
    row["exposures"][0]["resourse"] = ["scopes"]
    assert 'unknown property "resourse"' in _errors_with_probe(row)


def test_every_referenced_type_is_named_in_types() -> None:
    unknown = sorted(
        f"{operation_id}: {name}"
        for operation_id, exposure in _exposures()
        for name in (exposure.get("returns"), (exposure.get("body") or {}).get("type"))
        if name and name not in _SURFACE["types"]
    )
    assert not unknown, f'Types used by an exposure but absent from "types": {unknown}'


def test_every_type_points_at_a_module_that_exports_it() -> None:
    missing = [
        f"{name} ({location['py']})"
        for name, location in _SURFACE["types"].items()
        if not hasattr(importlib.import_module(location["py"]), location.get("pyName", name))
    ]
    assert not missing, f"Types not exported from their declared module: {missing}"


def _resolve(root: object, exposure: dict) -> Optional[object]:
    target: object = root
    last = len(exposure["resource"]) - 1
    for index, name in enumerate(exposure["resource"]):
        target = getattr(target, _snake(name), None)
        if target is None:
            return None
        if "bind" in exposure and index == last:
            target = target("1")  # type: ignore[operator]
    return target


def _py_path(exposure: dict) -> str:
    resource = ".".join(_snake(part) for part in exposure["resource"])
    method = exposure.get("pyMethod") or _snake(exposure["method"])
    return f"{exposure['surface']}.{resource}.{method}"


def _resolves(root: object, exposure: dict) -> bool:
    method = exposure.get("pyMethod") or _snake(exposure["method"])
    return callable(getattr(_resolve(root, exposure), method, None))


def _unresolved(roots: Dict[str, object], skip: Set[str] = frozenset()) -> List[str]:
    return [
        f"{operation_id}: {_py_path(exposure)}"
        for operation_id, exposure in _exposures()
        if operation_id not in skip and not _resolves(roots[exposure["surface"]], exposure)
    ]


def _sync_clients() -> Dict[str, object]:
    return {
        "consumption": Modus(api_key="modus_x"),
        "management": ModusManagement(api_key="modus_x"),
    }


def _async_clients() -> Dict[str, object]:
    return {
        "consumption": AsyncModus(api_key="modus_x"),
        "management": AsyncModusManagement(api_key="modus_x"),
    }


def test_every_exposure_resolves_on_the_sync_clients() -> None:
    failures = _unresolved(_sync_clients())
    assert not failures, f"Exposures that do not resolve to a method: {failures}"


def test_every_exposure_resolves_on_the_async_clients() -> None:
    failures = _unresolved(_async_clients(), skip=_ASYNC_GAPS)
    assert not failures, f"Exposures that do not resolve to a method: {failures}"


def test_async_gaps_are_still_gaps() -> None:
    """``_ASYNC_GAPS`` suppresses the async check, so each entry must still be a real gap."""
    roots = _async_clients()
    resolved = sorted(
        f"{operation_id}: {_py_path(exposure)}"
        for operation_id, exposure in _exposures()
        if operation_id in _ASYNC_GAPS and _resolves(roots[exposure["surface"]], exposure)
    )
    assert not resolved, (
        "These exposures now resolve on the async client, so _ASYNC_GAPS is stale — delete "
        f"the operationId from it: {resolved}"
    )


def test_async_gaps_name_known_operations() -> None:
    """A renamed operationId would leave a dead entry that suppresses nothing, silently."""
    unknown = sorted(_ASYNC_GAPS - set(_SURFACE["operations"]))
    assert not unknown, f"_ASYNC_GAPS names operationIds absent from sdk-surface.json: {unknown}"


def test_sync_only_hints_match_the_exact_expected_async_gaps() -> None:
    assert {
        operation_id for operation_id, exposure in _exposures()
        if exposure.get("pyAsync") is False
    } == _ASYNC_GAPS
