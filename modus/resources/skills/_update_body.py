"""Internal-only Pydantic models for skills create/update request bodies."""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel


class _SkillCreateBody(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)
    name: str
    description: Optional[str] = None
    expected_output: Optional[str] = None
    instructions: Optional[List[str]] = None
    toolset: Optional[Dict[str, Any]] = None
    model: Optional[str] = None
    connection_set: Optional[List[Dict[str, Any]]] = None
    context_selections: Optional[List[Dict[str, Any]]] = None
    interfaces: Optional[List[Dict[str, Any]]] = None
    access_config: Optional[Dict[str, Any]] = None


class _SkillUpdateBody(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)
    name: Optional[str] = None
    description: Optional[str] = None
    expected_output: Optional[str] = None
    instructions: Optional[List[str]] = None
    toolset: Optional[Dict[str, Any]] = None
    model: Optional[str] = None
    connection_set: Optional[List[Dict[str, Any]]] = None
    context_selections: Optional[List[Dict[str, Any]]] = None
    interfaces: Optional[List[Dict[str, Any]]] = None
    access_config: Optional[Dict[str, Any]] = None
    manager_id: Optional[str] = None
