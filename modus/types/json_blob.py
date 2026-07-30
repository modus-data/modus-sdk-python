"""Open-ended JSON objects for integration-specific fields."""
from __future__ import annotations

from typing import Any, Dict, Union

from pydantic import BaseModel, ConfigDict

JsonObjectInput = Union["JsonObject", Dict[str, Any]]


class JsonObject(BaseModel):
    """Integration-specific object; schema varies by endpoint."""

    model_config = ConfigDict(extra="allow")

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> JsonObject:
        """Build an open-ended JSON object from a plain dict."""
        return cls.model_validate(data)


def dump_json_object(value: JsonObjectInput) -> Dict[str, Any]:
    if isinstance(value, JsonObject):
        return value.model_dump(by_alias=True, exclude_none=True)
    return value
