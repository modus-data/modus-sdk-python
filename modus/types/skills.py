"""Skill model for the consumption SDK."""

from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel

SkillStatus = Literal["draft", "active", "deleted"]


class Skill(BaseModel):
    """
    A Modus skill.

    Skills are AI agents you can run interactively.
    To configure a skill (instructions, model, tools), use modus.management.ModusManagement.
    """

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        extra="ignore",  # API sends many more fields — ignore silently
    )

    id: int
    slug: str
    name: str
    status: SkillStatus
    description: Optional[str] = None
    has_unpublished_changes: bool = Field(default=False, title="HasUnpublishedChanges")

    @property
    def is_active(self) -> bool:
        return self.status == "active"

    @property
    def is_draft(self) -> bool:
        return self.status == "draft"
