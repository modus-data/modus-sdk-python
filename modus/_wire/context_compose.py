"""Wire models for POST /api/v1/skills/{id}/context."""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel


class _ComposeSkillContextRequestWire(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        extra="ignore",
    )

    message: str
    limit: Optional[int] = None


class _ComposeSkillContextResponseWire(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        extra="ignore",
    )

    context_items: List[Dict[str, Any]] = Field(alias="contextItems")
    original_count: int = Field(alias="originalCount")
    session_id: str = Field(alias="sessionId")
