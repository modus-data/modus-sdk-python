"""Context types for modus.management."""

from __future__ import annotations

from modus._generated.models import UpdateContextItemDto
from modus._generated.models import UserFeedback as UserFeedbackEnum
from modus.types.context import (
    ContextItem,
    ContextItemAccess,
    ContextItemAccessUpdate,
    ContextItemDeletion,
    ContextItemGroupPermission,
    ContextItemMove,
    ContextItemSharedUser,
    ContextItemSharePermission,
    ContextItemVisibility,
    ContextType,
    CreatedContextItem,
)

ContextItemUpdate = UpdateContextItemDto
UserFeedback = UserFeedbackEnum

__all__ = [
    "ContextItem",
    "ContextItemAccess",
    "ContextItemAccessUpdate",
    "ContextItemGroupPermission",
    "ContextItemSharedUser",
    "ContextItemSharePermission",
    "ContextItemVisibility",
    "ContextItemDeletion",
    "ContextItemMove",
    "ContextItemUpdate",
    "ContextType",
    "CreatedContextItem",
    "UpdateContextItemDto",
    "UserFeedback",
]
