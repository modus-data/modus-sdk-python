"""Wire helpers for setting guardrails on skills/agents (private)."""
from __future__ import annotations

from typing import Any, Dict, List, Optional

# Org-wide default group on the wire — matches @modus/permissions EVERYONE_GROUP_ID.
_EVERYONE_GROUP_ID = "__everyone__"


def access_config_wire_for_create(guardrails: List[str]) -> Dict[str, Any]:
    """Full accessConfig blob for create when the caller sets guardrails only.

    The API rejects partial accessConfig (guardrails-only). This matches the
    server default for a new shared skill except for the guardrails list.
    """
    return {
        "visibility": "shared",
        "groupPermissions": {_EVERYONE_GROUP_ID: {"use": True, "manage": True}},
        "guardrails": guardrails,
        "sharedWith": [],
    }


def access_config_wire_for_update(
    existing: Optional[Dict[str, Any]],
    guardrails: List[str],
) -> Dict[str, Any]:
    """Merge guardrails into the current accessConfig from a GET response."""
    if not existing:
        return access_config_wire_for_create(guardrails)
    merged = dict(existing)
    merged["guardrails"] = guardrails
    return merged
