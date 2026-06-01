"""Task-agent skill selection types."""
from __future__ import annotations

from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel

from ._serialize import dump_optional_model

AgentSelectionInput = Union["AgentSelection", Dict[str, Any]]


class AgentSelectionEntry(BaseModel):
    """One skill invoked as part of a task agent run."""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        extra="forbid",
    )

    agent_id: int = Field(ge=1)
    priority_order: int = Field(ge=1)
    role: Optional[str] = None
    instructions: Optional[str] = None
    tool_restrictions: Optional[List[str]] = None


class AgentSelection(BaseModel):
    """Ordered skills for a task-type agent."""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        extra="forbid",
    )

    agents: List[AgentSelectionEntry]
    model: Optional[str] = None

    @classmethod
    def single(cls, agent_id: int, *, model: Optional[str] = None) -> AgentSelection:
        return cls(agents=[AgentSelectionEntry(agent_id=agent_id, priority_order=1)], model=model)

    @classmethod
    def ordered(cls, agents: List[AgentSelectionEntry], *, model: Optional[str] = None) -> AgentSelection:
        return cls(agents=agents, model=model)


def dump_agent_selection(value: Optional[AgentSelectionInput]) -> Optional[Dict[str, Any]]:
    dumped = dump_optional_model(
        value,
        field_name="agent_selection",
        typed_label="AgentSelection",
        stacklevel=4,
    )
    return dumped if isinstance(dumped, dict) or dumped is None else None


def parse_agent_selection(raw: object) -> Optional[AgentSelection]:
    if raw is None:
        return None
    return AgentSelection.model_validate(raw)
