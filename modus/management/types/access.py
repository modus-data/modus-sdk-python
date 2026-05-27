"""AccessConfig — permission and guardrails wrapper."""
from __future__ import annotations
from typing import Any, Dict, List

from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel


class AccessConfig(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        extra="ignore",
    )

    guardrails: List[str] = []
    """Guardrail rule names applied to this skill/agent."""

    permissions: Dict[str, Any] = {}
    """Raw permissions dict — shape is backend-internal."""
