"""Serialize typed management inputs for HTTP bodies."""
from __future__ import annotations

from typing import Any, Dict, Optional, TypeVar, Union

from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


def dump_optional_model(
    value: Optional[T],
    *,
    field_name: str,
    typed_label: str,
) -> Optional[Dict[str, Any]]:
    """Serialize a typed model input, rejecting raw dicts.

    These fields have factory methods (for example ``Toolset.slack(...)``).
    A raw ``dict`` bypasses validation and couples callers to the wire shape,
    so it is rejected with a clear error pointing back to the factory.
    """
    if value is None:
        return None
    if isinstance(value, BaseModel):
        return value.model_dump(by_alias=True, exclude_none=True)
    raise TypeError(
        f"{field_name}= must be a {typed_label} built with its factory methods, "
        f"not {type(value).__name__}."
    )


def dump_opaque_json(
    value: Optional[Union[BaseModel, Dict[str, Any]]],
    *,
    field_name: str,
) -> Optional[Dict[str, Any]]:
    """Serialize a free-form JSON field that accepts a model or a plain dict.

    Used for genuinely structureless fields (workflow graphs, opaque JSON
    blobs) where a ``dict`` is the natural, honest input and there is no rich
    type to validate against.
    """
    if value is None:
        return None
    if isinstance(value, BaseModel):
        return value.model_dump(by_alias=True, exclude_none=True)
    if isinstance(value, dict):
        return value
    raise TypeError(
        f"{field_name}= must be a dict or model, not {type(value).__name__}."
    )
