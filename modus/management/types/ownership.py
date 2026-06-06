"""Ownership transfer types for skills and agents."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel

from modus._wire.pending_ownership_transfer import _PendingOwnershipTransferWire


class PendingOwnershipTransfer(BaseModel):
    """Pending ownership transfer awaiting recipient acceptance."""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        extra="ignore",
    )

    pending_owner_user_id: str
    pending_owner_email: Optional[str] = None
    requested_by_user_id: str
    requested_at: datetime


def parse_pending_ownership_transfer(
    wire: Optional[_PendingOwnershipTransferWire],
) -> Optional[PendingOwnershipTransfer]:
    if wire is None:
        return None
    return PendingOwnershipTransfer(
        pending_owner_user_id=wire.pending_owner_user_id,
        pending_owner_email=wire.pending_owner_email,
        requested_by_user_id=wire.requested_by_user_id,
        requested_at=wire.requested_at,
    )
