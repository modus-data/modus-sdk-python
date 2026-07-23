"""Suggested questions and first-party suggestion event tracking."""
from __future__ import annotations

from enum import Enum
from typing import Any, Mapping, Optional, Sequence, Union

from ..._config import ModusConfig
from ..._generated.models import SuggestionQuestionDto
from ..._http import AsyncHttpClient, HttpClient
from ..._openapi_invoke import invoke_operation, invoke_operation_async
from ..._pagination import (
    build_aip_page_mapped,
    build_async_aip_page_mapped,
)
from ..._retry import async_with_retry, with_retry
from ..._validation import validate_id, validate_page_size
from ...types.pagination import AsyncPage, Page
from ...types.suggestions import SuggestionEventSource, SuggestionEventType, SuggestionQuestion

DEFAULT_SUGGESTIONS_PAGE_SIZE = 5
MAX_SUGGESTIONS_PAGE_SIZE = 12


def _parse_suggestion(raw: dict) -> SuggestionQuestion:
    return SuggestionQuestionDto.model_validate(raw)


def _enum_value(value: Union[str, Enum]) -> str:
    return str(value.value) if isinstance(value, Enum) else value


def _list_params(
    page_size: int,
    page_token: Optional[str],
    scope_id: Optional[int],
    scope_ids: Optional[Sequence[int]],
) -> dict:
    params: dict[str, Any] = {"pageSize": page_size}
    if page_token is not None:
        params["pageToken"] = page_token
    if scope_id is not None:
        params["scopeId"] = scope_id
    if scope_ids is not None:
        params["scopeIds"] = ",".join(str(item) for item in scope_ids)
    return params


def _event_body(
    *,
    event_type: Union[SuggestionEventType, str],
    source: Optional[Union[SuggestionEventSource, str]],
    skill_id: Optional[int],
    thread_id: Optional[str],
    metadata: Optional[Mapping[str, Any]],
) -> dict:
    body: dict[str, Any] = {"eventType": _enum_value(event_type)}
    if source is not None:
        body["source"] = _enum_value(source)
    if skill_id is not None:
        body["skillId"] = skill_id
    if thread_id is not None:
        body["threadId"] = thread_id
    if metadata is not None:
        body["metadata"] = dict(metadata)
    return body


class SuggestionsResource:
    """List suggested questions and record suggestion events."""

    def __init__(self, http: HttpClient, config: ModusConfig) -> None:
        self._http = http
        self._config = config

    def list(
        self,
        *,
        page_size: int = DEFAULT_SUGGESTIONS_PAGE_SIZE,
        page_token: Optional[str] = None,
        scope_id: Optional[int] = None,
        scope_ids: Optional[Sequence[int]] = None,
    ) -> Page[SuggestionQuestion]:
        """List approved suggested questions for the caller organization.

        Args:
            page_size: Maximum number of suggestions to return.
            page_token: Cursor from a previous page, if any.
            scope_id: Optional single scope id filter.
            scope_ids: Optional multi-scope id filter (comma-joined on the wire).
        """
        validate_page_size(page_size, max_page_size=MAX_SUGGESTIONS_PAGE_SIZE)
        return self._list_page(page_size, page_token, scope_id, scope_ids)

    def _list_page(
        self,
        page_size: int,
        page_token: Optional[str],
        scope_id: Optional[int],
        scope_ids: Optional[Sequence[int]],
    ) -> Page[SuggestionQuestion]:
        data = with_retry(
            lambda: invoke_operation(
                self._http,
                "SuggestionsController_listApproved",
                query=_list_params(page_size, page_token, scope_id, scope_ids),
            ),
            self._config.max_retries,
        )
        return build_aip_page_mapped(
            data,
            "suggestions",
            _parse_suggestion,
            lambda cur: self._list_page(page_size, cur, scope_id, scope_ids),
        )

    def record_event(
        self,
        suggestion_id: str,
        *,
        event_type: Union[SuggestionEventType, str],
        source: Optional[Union[SuggestionEventSource, str]] = None,
        skill_id: Optional[int] = None,
        thread_id: Optional[str] = None,
        metadata: Optional[Mapping[str, Any]] = None,
    ) -> None:
        """Record that a suggested question was shown, clicked, dismissed, or submitted."""
        validate_id(suggestion_id, name="suggestion_id")
        body = _event_body(
            event_type=event_type,
            source=source,
            skill_id=skill_id,
            thread_id=thread_id,
            metadata=metadata,
        )
        with_retry(
            lambda: invoke_operation(
                self._http,
                "SuggestionsController_recordEvent",
                path_params={"id": suggestion_id},
                json_body=body,
            ),
            self._config.max_retries,
        )


class AsyncSuggestionsResource:
    """Async suggested-question APIs."""

    def __init__(self, http: AsyncHttpClient, config: ModusConfig) -> None:
        self._http = http
        self._config = config

    async def list(
        self,
        *,
        page_size: int = DEFAULT_SUGGESTIONS_PAGE_SIZE,
        page_token: Optional[str] = None,
        scope_id: Optional[int] = None,
        scope_ids: Optional[Sequence[int]] = None,
    ) -> AsyncPage[SuggestionQuestion]:
        """List approved suggested questions for the caller organization.

        Args:
            page_size: Maximum number of suggestions to return.
            page_token: Cursor from a previous page, if any.
            scope_id: Optional single scope id filter.
            scope_ids: Optional multi-scope id filter (comma-joined on the wire).
        """
        validate_page_size(page_size, max_page_size=MAX_SUGGESTIONS_PAGE_SIZE)
        return await self._list_page(page_size, page_token, scope_id, scope_ids)

    async def _list_page(
        self,
        page_size: int,
        page_token: Optional[str],
        scope_id: Optional[int],
        scope_ids: Optional[Sequence[int]],
    ) -> AsyncPage[SuggestionQuestion]:
        data = await async_with_retry(
            lambda: invoke_operation_async(
                self._http,
                "SuggestionsController_listApproved",
                query=_list_params(page_size, page_token, scope_id, scope_ids),
            ),
            self._config.max_retries,
        )
        return build_async_aip_page_mapped(
            data,
            "suggestions",
            _parse_suggestion,
            lambda cur: self._list_page(page_size, cur, scope_id, scope_ids),
        )

    async def record_event(
        self,
        suggestion_id: str,
        *,
        event_type: Union[SuggestionEventType, str],
        source: Optional[Union[SuggestionEventSource, str]] = None,
        skill_id: Optional[int] = None,
        thread_id: Optional[str] = None,
        metadata: Optional[Mapping[str, Any]] = None,
    ) -> None:
        """Record that a suggested question was shown, clicked, dismissed, or submitted."""
        validate_id(suggestion_id, name="suggestion_id")
        body = _event_body(
            event_type=event_type,
            source=source,
            skill_id=skill_id,
            thread_id=thread_id,
            metadata=metadata,
        )
        await async_with_retry(
            lambda: invoke_operation_async(
                self._http,
                "SuggestionsController_recordEvent",
                path_params={"id": suggestion_id},
                json_body=body,
            ),
            self._config.max_retries,
        )
