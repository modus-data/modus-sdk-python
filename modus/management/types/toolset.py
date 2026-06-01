"""Skill toolset types."""
from __future__ import annotations

from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel

from ._serialize import dump_optional_model

ToolsetInput = Union["Toolset", Dict[str, Any]]


class ToolsetTool(BaseModel):
    """One tool entry in a skill toolset."""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        extra="forbid",
    )

    id: str
    enabled: bool = True
    config: Optional[Dict[str, Any]] = None


class Toolset(BaseModel):
    """Tools a skill may invoke at run time."""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        extra="allow",
    )

    tools: List[ToolsetTool] = Field(default_factory=list)

    @classmethod
    def from_tools(cls, tools: List[ToolsetTool]) -> Toolset:
        return cls(tools=tools)

    @classmethod
    def empty(cls) -> Toolset:
        return cls(tools=[])


def dump_toolset(value: Optional[ToolsetInput]) -> Optional[Dict[str, Any]]:
    dumped = dump_optional_model(
        value, field_name="toolset", typed_label="Toolset", stacklevel=4
    )
    return dumped if isinstance(dumped, dict) or dumped is None else None


def parse_toolset(raw: object) -> Optional[Toolset]:
    if raw is None:
        return None
    return Toolset.model_validate(raw)
