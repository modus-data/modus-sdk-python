"""Workflow graph JSON for workflow-type agents."""
from __future__ import annotations

from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel

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
        return cls.model_validate(data)


def dump_workflow_structure(
    value: Optional[WorkflowGraphInput],
) -> Optional[Dict[str, Any]]:
    return dump_opaque_json(value, field_name="workflow_structure")


def parse_workflow_structure(raw: object) -> Optional[WorkflowGraph]:
    if raw is None:
        return None
    return WorkflowGraph.model_validate(raw)
