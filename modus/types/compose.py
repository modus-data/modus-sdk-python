"""Types for skill context composition responses."""
from __future__ import annotations

from typing import Any, Dict

from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel


class ContextComposeItem(BaseModel):
    """One context item returned from skill context composition."""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        extra="allow",
    )

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> ContextComposeItem:
        return cls.model_validate(data)
