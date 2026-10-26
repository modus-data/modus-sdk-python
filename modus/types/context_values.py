"""Rows returned by context item list_values."""
from __future__ import annotations

from typing import Any, Dict

from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel


class ContextValueRow(BaseModel):
    """One element of a context item's array field.

    Attributes:
        index: Position of the element in the array (0-based).
        value: The element itself, as JSON of any type.
    """

    index: int
    value: Any

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        extra="allow",
    )

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> ContextValueRow:
        """Build a value row from a plain dict."""
        return cls.model_validate(data)
