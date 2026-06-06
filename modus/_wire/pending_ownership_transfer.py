"""Wire model for PendingOwnershipTransferDto."""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel


class _PendingOwnershipTransferWire(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        extra="ignore",
    )

    pending_owner_user_id: str
    pending_owner_email: Optional[str] = None
    requested_by_user_id: str
    requested_at: datetime
