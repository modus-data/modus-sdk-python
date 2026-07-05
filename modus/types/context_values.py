"""Rows returned by context item list_values."""
from __future__ import annotations

from typing import Any, Dict

from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel


class ContextValueRow(BaseModel):
    """One value entry for a context item (shape varies by context type)."""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        extra="allow",
    )

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> ContextValueRow:
        return cls.model_validate(data)
