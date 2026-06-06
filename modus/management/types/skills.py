"""Skill model for the management SDK — flat, variation fields at top level."""

from __future__ import annotations

from datetime import datetime
from typing import List, Literal, Optional

from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel

from .access import AccessConfig
from .json_blob import JsonObject
from .ownership import PendingOwnershipTransfer
from .toolset import Toolset

SkillStatus = Literal["draft", "active", "deleted"]


class Skill(BaseModel):
    """
    A Modus skill with full configuration detail.

    Configuration fields (instructions, model, toolset, etc.) are populated
    only when fetching a single skill via mgmt.skills.get(id). They are None
    on list rows from mgmt.skills.list().

    To invoke a skill interactively, use modus-sdk (the consumption SDK).
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
    status: SkillStatus
    description: Optional[str] = None
    org_uuid: str

    # Version state
    has_unpublished_changes: bool
    active_variation_id: Optional[str] = None
    draft_variation_id: Optional[str] = None

    # Configuration — from variation, None on list rows, populated on .get()
    instructions: Optional[List[str]] = None
    model: Optional[str] = None
    expected_output: Optional[str] = None
    toolset: Optional[Toolset] = None
    connection_set: Optional[List[JsonObject]] = None
    context_selections: Optional[List[JsonObject]] = None
    interfaces: Optional[List[JsonObject]] = None
    evaluations: Optional[List[JsonObject]] = None

    # Guardrails — from accessConfig, always present (default [])
    guardrails: List[str] = []

    # Full access config
    access_config: AccessConfig = AccessConfig()

    # Ownership transfer in flight (populated on .get() when present)
    pending_ownership_transfer: Optional[PendingOwnershipTransfer] = None

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
