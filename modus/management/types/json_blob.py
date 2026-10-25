"""Open-ended JSON objects for integration-specific fields.

These fields are genuinely free-form on the backend (it stores opaque JSON),
so a plain ``dict`` is the natural input. ``JsonObject`` is offered as an
optional convenience wrapper; both are accepted.
"""
from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel

from modus.types.json_blob import JsonObject, JsonObjectInput

from ._serialize import dump_opaque_json

# A generated row model (for example ConnectionSetItemDto from scopes.get) is a
# BaseModel. Sequence is covariant, so a list of that model is accepted here.
JsonObjectListInput = Sequence[Union[BaseModel, Mapping[str, Any]]]

__all__ = ["JsonObject", "JsonObjectInput", "JsonObjectListInput"]


def dump_json_object(value: Optional[JsonObjectInput]) -> Optional[Dict[str, Any]]:
    return dump_opaque_json(value, field_name="value")


def dump_json_object_list(
    value: Optional[JsonObjectListInput],
    *,
    field_name: str,
) -> Optional[List[Dict[str, Any]]]:
    if value is None:
        return None
    if not value:
        return []
    normalized: List[Dict[str, Any]] = []
    for item in value:
        if isinstance(item, BaseModel):
            # by_alias keeps connection_id (the pinned wire name). exclude_none
            # drops only absent optionals; required keys such as path stay, including [].
            normalized.append(item.model_dump(by_alias=True, exclude_none=True))
        elif isinstance(item, Mapping):
            normalized.append(dict(item))
        else:
            raise TypeError(
                f"{field_name} items must be a model or mapping, got {type(item).__name__}"
            )
    return normalized


def parse_json_object_list(raw: object) -> Optional[List[JsonObject]]:
    if raw is None:
        return None
    if not isinstance(raw, list):
        return None
    return [JsonObject.model_validate(item) for item in raw]
