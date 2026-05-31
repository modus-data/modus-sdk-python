"""Public types for skill context composition."""
from __future__ import annotations

from typing import Any, Dict, List

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel


class SkillContextComposition(BaseModel):
    """Result of POST /api/v1/skills/{id}/context (RAG compose, no LLM)."""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        extra="allow",
    )

    context_items: List[Dict[str, Any]]
    original_count: int
    session_id: str
