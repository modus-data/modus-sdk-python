"""
OpenAPI list-response contract: registry items_key matches List*ResponseDto schemas.
"""
from __future__ import annotations

from typing import Any, Set

import pytest

from .list_operations import (
    FORBIDDEN_RESPONSE_KEYS,
    REJECTED_LIST_RESPONSE_BODY,
    SDK_AIP_LIST_OPERATIONS,
)


def _operation_response_schema_name(openapi: dict, operation_id: str) -> str:
    for path_item in openapi.get("paths", {}).values():
        for method, op in path_item.items():
            if method not in ("get", "post", "put", "patch", "delete"):
                continue
            if not isinstance(op, dict) or op.get("operationId") != operation_id:
                continue
            responses = op.get("responses", {})
            ok = responses.get("200") or responses.get("201")
            if not ok:
                raise KeyError(f"{operation_id}: no 200/201 response")
            content = ok.get("content", {}).get("application/json", {})
            ref = content.get("schema", {}).get("$ref", "")
            if not ref.startswith("#/components/schemas/"):
                raise KeyError(f"{operation_id}: unexpected response schema ref {ref!r}")
            return ref.rsplit("/", 1)[-1]
    raise KeyError(f"operationId {operation_id!r} not found in OpenAPI spec")


def _list_response_array_keys(openapi: dict, schema_name: str) -> Set[str]:
    schema = openapi["components"]["schemas"][schema_name]
    props = schema.get("properties", {})
    required = set(schema.get("required", []))
    array_keys = {
        name
        for name, prop in props.items()
        # Release N dual envelopes mark the old plural deprecated; SDK items_key is canonical.
        if prop.get("type") == "array"
        and name in required
        and prop.get("deprecated") is not True
    }
    return array_keys


@pytest.mark.parametrize(
    "spec",
    SDK_AIP_LIST_OPERATIONS,
    ids=lambda s: f"{s.operation_id}:{s.client_kind}",
)
def test_registry_items_key_matches_openapi_response_dto(
    openapi: dict,
    spec: Any,
) -> None:
    schema_name = _operation_response_schema_name(openapi, spec.operation_id)
    array_keys = _list_response_array_keys(openapi, schema_name)
    assert array_keys == {spec.items_key}, (
        f"{spec.operation_id} ({schema_name}): expected single required array "
        f"{spec.items_key!r}, OpenAPI has {sorted(array_keys)}"
    )
    schema = openapi["components"]["schemas"][schema_name]
    props = schema["properties"]
    assert "nextPageToken" in props, (
        f"{schema_name} must expose nextPageToken for AIP-158 pagination"
    )


@pytest.mark.parametrize(
    "spec",
    SDK_AIP_LIST_OPERATIONS,
    ids=lambda s: f"{s.operation_id}:{s.client_kind}",
)
def test_registry_items_key_not_forbidden_plural(spec: Any) -> None:
    assert spec.items_key not in FORBIDDEN_RESPONSE_KEYS


def test_rejected_fixture_uses_forbidden_keys() -> None:
    assert "items" in REJECTED_LIST_RESPONSE_BODY
    assert "nextCursor" in REJECTED_LIST_RESPONSE_BODY
    assert "nextPageToken" not in REJECTED_LIST_RESPONSE_BODY
