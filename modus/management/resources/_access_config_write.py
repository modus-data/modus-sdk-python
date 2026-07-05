"""Resolve accessConfig wire blobs for guardrails= writes (private)."""
from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional

from ..types._guardrails_access import (
    access_config_wire_for_create,
    access_config_wire_for_update,
)


def _access_from_response(raw: Dict[str, Any]) -> Dict[str, Any]:
    value = raw.get("accessConfig") or raw.get("access_config") or {}
    return value if isinstance(value, dict) else {}


def access_config_body_for_create(
    guardrails: Optional[List[str]],
) -> Optional[Dict[str, Any]]:
    if guardrails is None:
        return None
    return access_config_wire_for_create(guardrails)


def access_config_body_for_update(
    guardrails: Optional[List[str]],
    load_resource: Callable[[], Dict[str, Any]],
) -> Optional[Dict[str, Any]]:
    if guardrails is None:
        return None
    return access_config_wire_for_update(_access_from_response(load_resource()), guardrails)
