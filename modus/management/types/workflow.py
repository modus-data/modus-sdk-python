"""Workflow graph JSON for workflow-type agents."""
from __future__ import annotations

from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel

from modus._generated.models import WorkflowStructureDto

from ._serialize import dump_opaque_json

WorkflowGraphInput = Union["WorkflowGraph", Dict[str, Any]]


class WorkflowGraph(BaseModel):
    """
    Workflow graph (``nodes`` + ``edges``) for ``type=\"workflow\"`` agents.

    The API stores free-form JSONB; this type validates top-level keys when
  present but allows additional fields.
    """

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        extra="allow",
    )

    nodes: Optional[List[Any]] = None
    edges: Optional[List[Any]] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> WorkflowGraph:
        """Build a workflow graph from a plain dict.

        Args:
            data: Dict with ``nodes`` and ``edges`` keys (plus optional extras).

        Returns:
            Validated ``WorkflowGraph`` instance.
        """
        return cls.model_validate(data)


def dump_workflow_structure(
    value: Optional[WorkflowGraphInput],
) -> Optional[Dict[str, Any]]:
    return dump_opaque_json(value, field_name="workflow_structure")


def parse_workflow_structure(raw: object) -> Optional[WorkflowGraph]:
    if raw is None:
        return None
    if isinstance(raw, WorkflowGraph):
        return raw
    # GET types the graph as WorkflowStructureResponseDto, a sibling of the
    # request DTO. Both dump to the camelCase wire (`sourceHandle`).
    if isinstance(raw, BaseModel) and not isinstance(raw, WorkflowStructureDto):
        raw = raw.model_dump(by_alias=True, exclude_none=True)
    dto = WorkflowStructureDto.model_validate(raw)
    # The graph wire uses camelCase (`sourceHandle`). A field-name dump
    # renames that key, and the next update is rejected.
    return WorkflowGraph.model_validate(dto.model_dump(by_alias=True, exclude_none=True))
