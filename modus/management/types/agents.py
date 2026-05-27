"""Agent model for the management SDK — flat, variation fields at top level."""

from __future__ import annotations
from datetime import datetime
from typing import List, Literal, Optional

from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel

from .access import AccessConfig

AgentStatus = Literal["draft", "active", "deleted"]
AgentType = Literal["task", "workflow"]


class Agent(BaseModel):
    """
    A Modus agent (automation) with full configuration detail.

    Configuration fields (instructions, model) are populated only when
    fetching a single agent via mgmt.agents.get(id). They are None on list rows.

    To invoke an agent, use modus-sdk (the consumption SDK).
    """

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        extra="ignore",
    )

    # Identity
    id: int
    slug: str
    name: str
    status: AgentStatus
    type: AgentType
    description: Optional[str] = None
    org_uuid: str

    # Version state
    has_unpublished_changes: bool
    is_enabled: bool = False
    active_variation_id: Optional[str] = None
    draft_variation_id: Optional[str] = None

    # Configuration — from variation, None on list rows, populated on .get()
    instructions: Optional[List[str]] = None
    model: Optional[str] = None

    # Guardrails
    guardrails: List[str] = []

    # Full access config
    access_config: AccessConfig = AccessConfig()

    # Timestamps
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None

    @property
    def is_active(self) -> bool:
        return self.status == "active"

    @property
    def is_draft(self) -> bool:
        return self.status == "draft"
