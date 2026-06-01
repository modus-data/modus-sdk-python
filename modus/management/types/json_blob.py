"""Open-ended JSON objects for integration-specific fields."""
from __future__ import annotations

from typing import Any, Dict, List, Optional, Union, cast

from modus.types.json_blob import JsonObject, JsonObjectInput

from ._serialize import dump_optional_model

JsonObjectListInput = Union[List[JsonObject], List[Dict[str, Any]]]

__all__ = ["JsonObject", "JsonObjectInput", "JsonObjectListInput"]


def dump_json_object(value: Optional[JsonObjectInput]) -> Optional[Dict[str, Any]]:
    dumped = dump_optional_model(
        value, field_name="value", typed_label="JsonObject", stacklevel=4
    )
    return dumped if isinstance(dumped, dict) or dumped is None else None


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
    saw_raw_dict = False
    for item in value:
        if isinstance(item, JsonObject):
            normalized.append(item.model_dump(by_alias=True, exclude_none=True))
        elif isinstance(item, dict):
            saw_raw_dict = True
            normalized.append(item)
        else:
            raise TypeError(
                f"{field_name} items must be JsonObject or dict, got {type(item).__name__}"
            )
    if saw_raw_dict:
        dump_optional_model(
            cast(List[Dict[str, Any]], normalized),
            field_name=field_name,
            typed_label="JsonObject",
            stacklevel=4,
        )
    return normalized


def parse_json_object_list(raw: object) -> Optional[List[JsonObject]]:
    if raw is None:
        return None
    if not isinstance(raw, list):
        return None
    return [JsonObject.model_validate(item) for item in raw]
