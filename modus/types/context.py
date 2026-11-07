"""Context types — re-exported from OpenAPI DTOs."""

from __future__ import annotations

from typing import List, Optional, TypedDict

from .._generated.models import (
    ContextItemAccessDto,
    ContextItemAccessResponseDto,
    ContextItemAncestorDto,
    ContextItemDto,
    ContextItemGroupPermissionDto,
    ContextItemSharedUserDto,
    ContextItemSharePermission,
    ContextItemVisibility,
    CreateCustomContextItemDto,
    CreateCustomContextItemRelationDto,
    CreatedContextItemResponseDto,
    CustomAttributeDto,
    CustomContextItemKind,
    DeleteContextItemResponseDto,
    LookupContextItemRowDto,
    MoveContextItemResponseDto,
    UpdateCustomContextItemDto,
)

ContextItem = ContextItemDto
ContextItemAncestor = ContextItemAncestorDto
ContextItemLookupRow = LookupContextItemRowDto
ContextItemDeletion = DeleteContextItemResponseDto
ContextItemMove = MoveContextItemResponseDto
ContextItemAccess = ContextItemAccessDto
ContextItemAccessUpdate = ContextItemAccessResponseDto
ContextItemGroupPermission = ContextItemGroupPermissionDto
ContextItemSharedUser = ContextItemSharedUserDto


class CreatedContextItem(CreatedContextItemResponseDto):
    """Create response with ``uid`` aliased to ``context_item_id`` for list/get parity."""

    @property
    def uid(self) -> str:
        """Context item UUID — same value as ``context_item_id`` on create responses."""
        return self.context_item_id


class CreatedCustomContextItem(TypedDict):
    """``custom_items.create`` result: the API's response, plus ``uid``."""

    contextItemId: str
    uid: str
    """Same value as ``contextItemId``: prefer it in new code (list/get parity)."""
    contextType: str
    dataPath: List[str]
    title: Optional[str]


class UpdatedCustomContextItem(TypedDict):
    """``custom_items.update`` result."""

    uid: str


# OpenAPI context_type is a string; keep a loose alias for annotations in user code.
ContextType = str

__all__ = [
    "ContextItem",
    "ContextItemAccess",
    "ContextItemAccessUpdate",
    "ContextItemGroupPermission",
    "ContextItemSharedUser",
    "ContextItemSharePermission",
    "ContextItemVisibility",
    "ContextItemAncestor",
    "ContextItemAncestorDto",
    "ContextItemDeletion",
    "ContextItemMove",
    "ContextItemDto",
    "ContextItemLookupRow",
    "ContextType",
    "CreateCustomContextItemDto",
    "CreateCustomContextItemRelationDto",
    "CreatedContextItem",
    "CreatedCustomContextItem",
    "CustomAttributeDto",
    "CustomContextItemKind",
    "LookupContextItemRowDto",
    "UpdateCustomContextItemDto",
    "UpdatedCustomContextItem",
]
