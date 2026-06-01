"""Public types for skill context composition."""
from __future__ import annotations

from typing import List

from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel

from .._wire.context_compose import _ComposeSkillContextResponseWire
from .compose import ContextComposeItem


class SkillContextComposition(BaseModel):
    """Context items Modus selected for a skill query (no chat response)."""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        extra="allow",
    )

    context_items: List[ContextComposeItem]
    original_count: int
    session_id: str


def composition_from_wire(wire: _ComposeSkillContextResponseWire) -> SkillContextComposition:
    """Build public composition from API response."""
    return SkillContextComposition(
        context_items=[ContextComposeItem.model_validate(item) for item in wire.context_items],
        original_count=wire.original_count,
        session_id=wire.session_id,
    )
