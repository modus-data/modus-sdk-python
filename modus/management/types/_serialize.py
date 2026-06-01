"""Serialize typed management inputs for HTTP bodies."""
from __future__ import annotations

import warnings
from typing import Any, Dict, List, Optional, TypeVar, Union

from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


def dump_optional_model(
    value: Optional[Union[T, Dict[str, Any], List[Dict[str, Any]]]],
    *,
    field_name: str,
    typed_label: str,
    stacklevel: int = 3,
) -> Optional[Any]:
    if value is None:
        return None
    if isinstance(value, BaseModel):
        return value.model_dump(by_alias=True, exclude_none=True)
    if isinstance(value, list) and value and isinstance(value[0], BaseModel):
        return [item.model_dump(by_alias=True, exclude_none=True) for item in value]
    if isinstance(value, (dict, list)):
        warnings.warn(
            f"Passing a raw dict/list for {field_name}= is deprecated; use {typed_label}.",
            DeprecationWarning,
            stacklevel=stacklevel,
        )
        return value
    return value
