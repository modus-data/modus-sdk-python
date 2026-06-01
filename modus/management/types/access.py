"""AccessConfig — permission and guardrails wrapper."""
from __future__ import annotations

from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel

from ._serialize import dump_optional_model

AccessConfigInput = Union["AccessConfig", Dict[str, Any]]


class AccessConfig(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        extra="ignore",
    )

    guardrails: List[str] = []
    """Guardrail rule names applied to this skill/agent."""

    permissions: Dict[str, Any] = {}
    """Raw permissions dict — shape is backend-internal."""

    @classmethod
    def with_guardrails(cls, guardrails: List[str]) -> AccessConfig:
        return cls(guardrails=guardrails)


def dump_access_config(value: Optional[AccessConfigInput]) -> Optional[Dict[str, Any]]:
    dumped = dump_optional_model(
        value,
        field_name="access_config",
        typed_label="AccessConfig",
        stacklevel=4,
    )
    return dumped if isinstance(dumped, dict) or dumped is None else None
