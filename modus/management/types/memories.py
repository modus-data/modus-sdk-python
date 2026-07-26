"""Skill memory types."""
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel


class Memory(BaseModel):
    """One memory stored for a skill."""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        extra="ignore",
    )

    id: str
    memory: str
    hash: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class MemorySearchRequest(BaseModel):
    """Search query for a skill's stored memories."""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        extra="forbid",
    )

    query: str = Field(min_length=1)
    user_id: Optional[str] = None
    limit: Optional[int] = Field(default=None, ge=1, le=1000)


class MemoryUpdate(BaseModel):
    """Fields for updating a skill memory."""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        extra="forbid",
    )

    memory: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

    @classmethod
    def text_only(cls, memory: str) -> MemoryUpdate:
        """Update only the memory text, leaving metadata unchanged.

        Args:
            memory: Replacement memory text.
        """
        return cls(memory=memory)


class MemorySearchResult(BaseModel):
    """Memories returned from a list or search call."""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        extra="ignore",
    )

    memories: List[Memory] = Field(default_factory=list)
    next_page_token: Optional[str] = None
