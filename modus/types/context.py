"""Context types — re-exported from OpenAPI DTOs."""

from __future__ import annotations

from .._generated.models import (
    ContextItemDto,
    CreatedContextItemResponseDto,
    DeleteContextItemResponseDto,
    LookupContextItemRowDto,
)

ContextItem = ContextItemDto
ContextItemLookupRow = LookupContextItemRowDto
ContextItemDeletion = DeleteContextItemResponseDto


class CreatedContextItem(CreatedContextItemResponseDto):
    """Create response with ``uid`` aliased to ``context_item_id`` for list/get parity."""

    @property
    def uid(self) -> str:
        return self.context_item_id


# OpenAPI context_type is a string; keep a loose alias for annotations in user code.
ContextType = str

__all__ = [
    "ContextItem",
    "ContextItemDeletion",
    "ContextItemDto",
    "ContextItemLookupRow",
    "ContextType",
    "CreatedContextItem",
    "LookupContextItemRowDto",
]
