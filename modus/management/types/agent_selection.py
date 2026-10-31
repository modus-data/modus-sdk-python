"""Task-agent skill selection types."""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel

from modus._generated.models import AgentSelectionDto, ModelSettingsDto


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
    model_settings: Optional[ModelSettingsDto] = None

    @classmethod
    def single(cls, agent_id: int, *, model: Optional[str] = None) -> AgentSelection:
        """Select one scope for a task workflow.

        Args:
            agent_id: Scope id to invoke.
            model:    Optional override model for this run.
        """
        return cls(agents=[AgentSelectionEntry(agent_id=agent_id, priority_order=1)], model=model)

    @classmethod
    def ordered(cls, agents: List[AgentSelectionEntry], *, model: Optional[str] = None) -> AgentSelection:
        """Select multiple scopes in priority order for a task workflow.

        Args:
            agents: Ordered scope entries with priority.
            model:  Optional override model for this run.
        """
        return cls(agents=agents, model=model)


AgentSelectionInput = AgentSelection


def dump_agent_selection(value: Optional[AgentSelectionInput]) -> Optional[Dict[str, Any]]:
    if value is None:
        return None
    if not isinstance(value, AgentSelection):
        raise TypeError(
            "agent_selection= must be an AgentSelection built with its factory methods "
            f"(for example AgentSelection.single(agent_id)), not {type(value).__name__}."
        )
    # The agents API validates agent_selection with snake_case keys
    # (agent_id, priority_order, ...), unlike the camelCase top-level body,
    # except modelSettings, which it stores under its camelCase keys.
    body = value.model_dump(by_alias=False, exclude_none=True, exclude={"model_settings"})
    if value.model_settings is not None:
        body["modelSettings"] = value.model_settings.model_dump(mode="json", by_alias=True, exclude_none=True)
    return body


def parse_agent_selection(raw: object) -> Optional[AgentSelection]:
    if raw is None:
        return None
    if isinstance(raw, AgentSelection):
        return raw
    # GET types the selection as AgentSelectionResponseDto. Field names stay
    # snake_case (`agent_id`); camelCase aliases are rejected on the next write.
    if isinstance(raw, BaseModel) and not isinstance(raw, AgentSelectionDto):
        raw = raw.model_dump(by_alias=False, exclude_none=True)
    dto = AgentSelectionDto.model_validate(raw)
    # Field names, not camelCase aliases: the agents API stores agent_id.
    return AgentSelection.model_validate(dto.model_dump(by_alias=False, exclude_none=True))
