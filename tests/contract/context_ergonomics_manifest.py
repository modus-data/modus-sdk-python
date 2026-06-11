"""Machine-readable ergonomic layering policy for context creators.

Register new create/update pairs and read accessors here; enforced by
``test_context_ergonomics.py``.
"""
from __future__ import annotations

# Paired create/update on mgmt.context (Tier C)
CREATOR_UPDATE_PAIRS: dict[str, tuple[str, str]] = {
    "note": ("create_note", "update_note"),
    "link": ("create_link", "update_link"),
    "saved_query": ("create_saved_query", "update_saved_query"),
}

# Read accessors per context_type (Tier B) — on modus.types.context_accessors
READ_ACCESSORS: dict[str, list[str]] = {
    "note": ["note_title", "note_body"],
    "link": ["link_title", "link_url"],
    "saved_query": ["saved_query_name", "saved_query_sql"],
}

# Shared cross-type accessors
SHARED_READ_ACCESSORS: list[str] = ["context_item_label", "is_verified"]
