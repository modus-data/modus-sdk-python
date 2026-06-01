"""Wire model for Skill — matches backend SkillDto exactly.
Private — do not import from user code.
"""
from __future__ import annotations
from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel


class _SkillWire(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        extra="ignore",  # ignore unknown API fields
    )

    id: int
    slug: str
    name: str
    status: str
    description: Optional[str] = None
    org_uuid: str
    has_unpublished_changes: bool
    active_variation_id: Optional[str] = None
    draft_variation_id: Optional[str] = None
    access_config: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None
    # Present on .get() only; absent (None) on list rows
    variation: Optional[Dict[str, Any]] = None
