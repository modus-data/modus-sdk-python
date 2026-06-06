"""Public types for skill context composition."""
from __future__ import annotations

from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel

from .._wire.context_compose import _ComposeSkillContextResponseWire


class SkillContextComposition(BaseModel):
    """Composed context Modus selected for a skill query (no chat response)."""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        extra="allow",
    )

    context: str
    original_count: int
    session_id: str


def composition_from_wire(wire: _ComposeSkillContextResponseWire) -> SkillContextComposition:
    """Build public composition from API response."""
    return SkillContextComposition(
        context=wire.context,
        original_count=wire.original_count,
        session_id=wire.session_id,
    )
