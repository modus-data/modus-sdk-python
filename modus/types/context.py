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
CreatedContextItem = CreatedContextItemResponseDto
ContextItemDeletion = DeleteContextItemResponseDto

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
