"""
Coverage guard: every OpenAPI GET with pageSize is in the SDK registry or excluded list.
"""
from __future__ import annotations

from typing import Set

from .list_operations import SDK_AIP_LIST_OPERATION_IDS, SDK_LIST_OPS_EXCLUDED


def _openapi_page_size_get_operation_ids(openapi: dict) -> Set[str]:
    found: Set[str] = set()
    for path_item in openapi.get("paths", {}).values():
        for method, op in path_item.items():
            if method != "get" or not isinstance(op, dict):
                continue
            operation_id = op.get("operationId")
            if not operation_id:
                continue
            query_names = {
                p.get("name")
                for p in op.get("parameters", [])
                if p.get("in") == "query" and "name" in p
            }
            if "pageSize" in query_names:
                found.add(operation_id)
    return found


def test_every_openapi_page_size_list_is_covered_or_excluded(openapi: dict) -> None:
    openapi_ops = _openapi_page_size_get_operation_ids(openapi)
    covered_or_excluded = SDK_AIP_LIST_OPERATION_IDS | SDK_LIST_OPS_EXCLUDED
    missing = openapi_ops - covered_or_excluded
    assert not missing, (
        "OpenAPI list operations with pageSize missing from SDK contract registry "
        f"(add to SDK_AIP_LIST_OPERATIONS or SDK_LIST_OPS_EXCLUDED): {sorted(missing)}"
    )
    unknown_excluded = SDK_LIST_OPS_EXCLUDED - openapi_ops
    assert not unknown_excluded, (
        f"SDK_LIST_OPS_EXCLUDED references unknown operationIds: {sorted(unknown_excluded)}"
    )
