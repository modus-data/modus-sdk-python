"""Assistant tool call payloads in conversation messages."""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel


class ToolCall(BaseModel):
    """One tool invocation on an assistant message."""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        extra="allow",
    )

    name: Optional[str] = None
    type: Optional[str] = None
    id: Optional[str] = None
    args: Optional[Dict[str, Any]] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> ToolCall:
        return cls.model_validate(data)


def parse_tool_calls(raw: object) -> Optional[List[ToolCall]]:
    if raw is None:
        return None
    if not isinstance(raw, list):
        return None
    return [ToolCall.model_validate(item) for item in raw]
