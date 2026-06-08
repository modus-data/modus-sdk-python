"""Every OpenAPI operation must be mapped in operation_coverage.OPERATIONS."""
from __future__ import annotations

from typing import Dict, Set

from .operation_coverage import OPERATIONS

_HTTP_METHODS = {"get", "post", "put", "patch", "delete"}


def _all_operation_ids(openapi: dict) -> Set[str]:
    ids: Set[str] = set()
    for path_item in openapi.get("paths", {}).values():
        for method, op in path_item.items():
            if method in _HTTP_METHODS and isinstance(op, dict) and op.get("operationId"):
                ids.add(op["operationId"])
    return ids


def test_every_spec_operation_is_mapped(openapi: dict) -> None:
    spec_ids = _all_operation_ids(openapi)
    unmapped = spec_ids - set(OPERATIONS)
    assert not unmapped, (
        "New OpenAPI operations are not mapped in tests/contract/operation_coverage.py. "
        "Add each to OPERATIONS and implement the HTTP method:\n"
        f"  {sorted(unmapped)}"
    )


def test_no_stale_mappings(openapi: dict) -> None:
    spec_ids = _all_operation_ids(openapi)
    stale = set(OPERATIONS) - spec_ids
    assert not stale, (
        "operation_coverage.py references operationIds that no longer exist in the spec "
        f"(remove or rename them): {sorted(stale)}"
    )


def test_operations_have_a_note() -> None:
    blank = [oid for oid, note in OPERATIONS.items() if not note.strip()]
    assert not blank, f"OPERATIONS entries missing a 'where exposed' note: {sorted(blank)}"


def test_exposure_summary_is_accurate(openapi: dict) -> None:
    spec_ids = _all_operation_ids(openapi)
    summary: Dict[str, int] = {
        "spec_total": len(spec_ids),
        "covered": len(OPERATIONS),
    }
    assert summary["covered"] == summary["spec_total"], summary
