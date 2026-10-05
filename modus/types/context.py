"""Context types — re-exported from OpenAPI DTOs."""

from __future__ import annotations

from .._generated.models import (
    ContextItemAncestorDto,
    ContextItemDto,
    CreatedContextItemResponseDto,
    DeleteContextItemResponseDto,
    LookupContextItemRowDto,
    MoveContextItemResponseDto,
)

ContextItem = ContextItemDto
ContextItemAncestor = ContextItemAncestorDto
ContextItemLookupRow = LookupContextItemRowDto
ContextItemDeletion = DeleteContextItemResponseDto
ContextItemMove = MoveContextItemResponseDto


class CreatedContextItem(CreatedContextItemResponseDto):
    """Create response with ``uid`` aliased to ``context_item_id`` for list/get parity."""

    @property
    def uid(self) -> str:
        """Context item UUID — same value as ``context_item_id`` on create responses."""
        return self.context_item_id


# OpenAPI context_type is a string; keep a loose alias for annotations in user code.
ContextType = str

__all__ = [
    "ContextItem",
    "ContextItemAncestor",
    "ContextItemAncestorDto",
    "ContextItemDeletion",
    "ContextItemMove",
    "ContextItemDto",
    "ContextItemLookupRow",
    "ContextType",
    "CreatedContextItem",
    "LookupContextItemRowDto",
]
