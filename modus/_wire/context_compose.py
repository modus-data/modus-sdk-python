"""Wire models for POST /api/v1/skills/{id}/context."""
from __future__ import annotations

from typing import Any, Optional

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

    context: str
    context_items: list[dict[str, Any]] = Field(
        default_factory=list,
        alias="contextItems",
        description="Deprecated; always empty. Use context.",
    )
    original_count: int = Field(alias="originalCount")
    session_id: str = Field(alias="sessionId")
