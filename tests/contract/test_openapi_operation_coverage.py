"""Every OpenAPI operation must be a deliberate decision: WRAPPED or INTERNAL.

This is the alignment guard. When the backend adds a new ``@PublicApi`` route,
this test fails until someone classifies it in ``operation_coverage.py`` — either
wrapping it in the SDK or recording why it stays app-only. That converts silent
drift into a required, reviewed decision.
"""
from __future__ import annotations

from typing import Dict, Set

from .operation_coverage import INTERNAL, WRAPPED

_HTTP_METHODS = {"get", "post", "put", "patch", "delete"}


def _all_operation_ids(openapi: dict) -> Set[str]:
    ids: Set[str] = set()
    for path_item in openapi.get("paths", {}).values():
        for method, op in path_item.items():
            if method in _HTTP_METHODS and isinstance(op, dict) and op.get("operationId"):
                ids.add(op["operationId"])
    return ids


def test_no_operation_classified_twice() -> None:
    overlap = set(WRAPPED) & set(INTERNAL)
    assert not overlap, f"Operations classified as both WRAPPED and INTERNAL: {sorted(overlap)}"


def test_every_spec_operation_is_classified(openapi: dict) -> None:
    spec_ids = _all_operation_ids(openapi)
    classified = set(WRAPPED) | set(INTERNAL)
    unclassified = spec_ids - classified
    assert not unclassified, (
        "New OpenAPI operations are not classified in tests/contract/operation_coverage.py. "
        "Decide for each: wrap it in the SDK (add to WRAPPED) or record why it stays app-only "
        f"(add to INTERNAL):\n  {sorted(unclassified)}"
    )


def test_no_stale_classifications(openapi: dict) -> None:
    spec_ids = _all_operation_ids(openapi)
    classified = set(WRAPPED) | set(INTERNAL)
    stale = classified - spec_ids
    assert not stale, (
        "operation_coverage.py references operationIds that no longer exist in the spec "
        f"(remove or rename them): {sorted(stale)}"
    )


def test_wrapped_operations_have_a_note() -> None:
    blank = [oid for oid, note in WRAPPED.items() if not note.strip()]
    assert not blank, f"WRAPPED entries missing a 'where exposed' note: {sorted(blank)}"


def test_internal_operations_have_a_reason() -> None:
    blank = [oid for oid, reason in INTERNAL.items() if not reason.strip()]
    assert not blank, f"INTERNAL entries missing a reason: {sorted(blank)}"


def test_exposure_summary_is_accurate(openapi: dict) -> None:
    # Guards the high-level "X wrapped / Y internal" numbers we report to users.
    spec_ids = _all_operation_ids(openapi)
    summary: Dict[str, int] = {
        "spec_total": len(spec_ids),
        "wrapped": len(WRAPPED),
        "internal": len(INTERNAL),
    }
    assert summary["wrapped"] + summary["internal"] == summary["spec_total"], summary
