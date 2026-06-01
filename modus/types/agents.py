"""Agent model for the consumption SDK."""

from __future__ import annotations
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel

AgentStatus = Literal["draft", "active", "deleted"]
AgentType = Literal["task", "workflow"]


class Agent(BaseModel):
    """
    A Modus agent (scheduled automation).

    Agents run unattended on a schedule or trigger.
    To configure an agent (instructions, model, trigger), use modus.management.ModusManagement.
    """

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        extra="ignore",
    )

    id: int
    slug: str
    name: str
    status: AgentStatus
    type: AgentType
    description: Optional[str] = None
    has_unpublished_changes: bool = Field(default=False, title="HasUnpublishedChanges")
    is_enabled: bool = Field(default=False, title="IsEnabled")

    @property
    def is_active(self) -> bool:
        return self.status == "active"

    @property
    def is_draft(self) -> bool:
        return self.status == "draft"
