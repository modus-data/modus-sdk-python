"""Agent model for the consumption SDK."""

from __future__ import annotations

from typing import List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel

AgentStatus = Literal["draft", "active", "deleted"]
AgentType = Literal["task", "workflow"]


class Agent(BaseModel):
    """
    A Modus agent (scheduled automation).

    Agents run unattended on a schedule or trigger.

    ``instructions`` and ``guardrails`` are populated on ``client.agents.get(id)``.
    ``guardrails`` is also present on list rows. To change configuration, use
    ``modus.management.ModusManagement``.
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

    # Read-only config surfaced for inspection (populated on .get(); guardrails on list too)
    instructions: Optional[List[str]] = None
    guardrails: List[str] = []

    @property
    def is_active(self) -> bool:
        return self.status == "active"

    @property
    def is_draft(self) -> bool:
        return self.status == "draft"
