"""Internal request body models for workflows create/update."""
from __future__ import annotations

from typing import Any, Dict, Optional

from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel


class _WorkflowCreateBody(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)
    name: str
    type: str  # "task" | "workflow"
    description: Optional[str] = None
    trigger: Optional[Dict[str, Any]] = None
    agent_selection: Optional[Dict[str, Any]] = None
    workflow_structure: Optional[Dict[str, Any]] = None
    access_config: Optional[Dict[str, Any]] = None


class _WorkflowUpdateBody(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)
    name: Optional[str] = None
    type: Optional[str] = None  # "task" | "workflow"
    description: Optional[str] = None
    trigger: Optional[Dict[str, Any]] = None
    agent_selection: Optional[Dict[str, Any]] = None
    workflow_structure: Optional[Dict[str, Any]] = None
    access_config: Optional[Dict[str, Any]] = None
