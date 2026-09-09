"""Types for immutable ingested-data uploads."""

from __future__ import annotations

from typing import Literal, TypedDict, Union

from modus._generated.models import CreatedIngestedDataResponseDto


class SqlIngestedDataRequest(TypedDict):
    """An executed SQL request whose response is being stored."""

    type: Literal["sql"]
    query: str


class _RequiredHttpIngestedDataRequest(TypedDict):
    type: Literal["http"]
    uri: str
    method: str


class HttpIngestedDataRequest(_RequiredHttpIngestedDataRequest, total=False):
    """An executed HTTP request whose response is being stored.

    Request headers are not accepted: they routinely carry credentials, and a
    name-based filter cannot reliably tell an auth header from an ordinary one.
    An omitted ``body`` is stored as an empty string.
    """

    body: str


IngestedDataRequest = Union[SqlIngestedDataRequest, HttpIngestedDataRequest]
IngestedDataResponseFormat = Literal["csv", "json", "xml", "text"]


class IngestedDataResponse(TypedDict):
    """Exact response content produced by an executed request."""

    format: IngestedDataResponseFormat
    content: str


IngestedDataUploadResult = CreatedIngestedDataResponseDto

__all__ = [
    "HttpIngestedDataRequest",
    "IngestedDataRequest",
    "IngestedDataResponse",
    "IngestedDataResponseFormat",
    "IngestedDataUploadResult",
    "SqlIngestedDataRequest",
]
