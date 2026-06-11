"""Shared chat path building and SSE stream session helpers."""
from __future__ import annotations

from typing import Any, AsyncIterator, Dict, Iterator, List, Optional, Union
from urllib.parse import quote

from ._exceptions import ModusError, RunCancelledError, StreamTimeoutError
from ._generated.models import SkillChatRequestDto, SkillChatResponseDto
from ._http import AsyncHttpClient, HttpClient
from ._streaming import parse_sse_stream
from ._validation import validate_chat_model, validate_id
from .types.chat import ChatResult
from .types.runs import (
    CancelledEvent,
    DoneEvent,
    ErrorEvent,
    RunEvent,
    StreamTimeoutEvent,
    TokenEvent,
)


def _effective_thread_id(thread_id: Optional[str]) -> Optional[str]:
    """Treat None and blank strings as "start a new thread"."""
    if thread_id is None:
        return None
    if isinstance(thread_id, str) and not thread_id.strip():
        return None
    return thread_id


def _chat_path(
    resource: str,
    resource_id: Union[int, str],
    *,
    thread_id: Optional[str],
    stream: bool,
) -> str:
    safe_id = quote(str(resource_id), safe="")
    suffix = "/stream" if stream else ""
    tid = _effective_thread_id(thread_id)
    if tid is not None:
        safe_tid = quote(str(tid), safe="")
        return f"/api/v1/{resource}/{safe_id}/conversations/{safe_tid}/chat{suffix}"
    return f"/api/v1/{resource}/{safe_id}/chat{suffix}"


def _chat_body(message: str, model: str) -> Dict[str, Any]:
    return SkillChatRequestDto(message=message, model=model).model_dump(  # type: ignore[arg-type]
        by_alias=True,
        exclude_none=True,
    )


def _raise_for_event(event: RunEvent) -> RunEvent:
    if isinstance(event, ErrorEvent):
        raise ModusError(event.message)
    if isinstance(event, CancelledEvent):
        raise RunCancelledError()
    if isinstance(event, StreamTimeoutEvent):
        raise StreamTimeoutError()
    return event


class ChatStream:
    """Sync context manager for SSE chat streams."""

    def __init__(
        self,
        http: HttpClient,
        path: str,
        body: Dict[str, Any],
    ) -> None:
        self._http = http
        self._path = path
        self._body = body
        self._final: Optional[ChatResult] = None
        self._text_parts: List[str] = []

    def __enter__(self) -> "ChatStream":
        return self

    def __exit__(self, *args: object) -> None:
        return None

    @property
    def text_stream(self) -> Iterator[str]:
        for event in self.event_stream:
            if isinstance(event, TokenEvent):
                yield event.content

    @property
    def event_stream(self) -> Iterator[RunEvent]:
        for line in self._http.stream_post(self._path, json=self._body):
            for event in parse_sse_stream(iter([line])):
                event = _raise_for_event(event)
                if isinstance(event, TokenEvent):
                    self._text_parts.append(event.content)
                if isinstance(event, DoneEvent):
                    content = "".join(self._text_parts)
                    self._final = SkillChatResponseDto(
                        content=content,
                        thread_id=event.thread_id,
                        run_id=event.run_id,
                    )
                    yield event
                    return
                yield event

    def get_final_result(self) -> ChatResult:
        if self._final is None:
            raise ModusError(
                "Stream ended without a done event; call get_final_result() only after "
                "consuming text_stream or event_stream."
            )
        return self._final


class AsyncChatStream:
    """Async context manager for SSE chat streams."""

    def __init__(
        self,
        http: AsyncHttpClient,
        path: str,
        body: Dict[str, Any],
    ) -> None:
        self._http = http
        self._path = path
        self._body = body
        self._final: Optional[ChatResult] = None
        self._text_parts: List[str] = []

    async def __aenter__(self) -> "AsyncChatStream":
        return self

    async def __aexit__(self, *args: object) -> None:
        return None

    @property
    def text_stream(self) -> AsyncIterator[str]:
        return self._text_stream_impl()

    async def _text_stream_impl(self) -> AsyncIterator[str]:
        async for event in self.event_stream:
            if isinstance(event, TokenEvent):
                yield event.content

    @property
    def event_stream(self) -> AsyncIterator[RunEvent]:
        return self._event_stream_impl()

    async def _event_stream_impl(self) -> AsyncIterator[RunEvent]:
        async for line in self._http.stream_post(self._path, json=self._body):
            for event in parse_sse_stream(iter([line])):
                event = _raise_for_event(event)
                if isinstance(event, TokenEvent):
                    self._text_parts.append(event.content)
                if isinstance(event, DoneEvent):
                    content = "".join(self._text_parts)
                    self._final = SkillChatResponseDto(
                        content=content,
                        thread_id=event.thread_id,
                        run_id=event.run_id,
                    )
                    yield event
                    return
                yield event

    def get_final_result(self) -> ChatResult:
        if self._final is None:
            raise ModusError(
                "Stream ended without a done event; call get_final_result() only after "
                "consuming text_stream or event_stream."
            )
        return self._final


def chat_buffered(
    http: HttpClient,
    resource: str,
    resource_id: Union[int, str],
    message: str,
    *,
    model: str,
    thread_id: Optional[str] = None,
) -> ChatResult:
    """POST buffered chat (JSON response)."""
    validate_id(resource_id, name=f"{resource}_id")
    validate_chat_model(model)
    path = _chat_path(resource, resource_id, thread_id=thread_id, stream=False)
    data = http.post(path, json=_chat_body(message, model))
    return SkillChatResponseDto.model_validate(data)


async def chat_buffered_async(
    http: AsyncHttpClient,
    resource: str,
    resource_id: Union[int, str],
    message: str,
    *,
    model: str,
    thread_id: Optional[str] = None,
) -> ChatResult:
    validate_id(resource_id, name=f"{resource}_id")
    validate_chat_model(model)
    path = _chat_path(resource, resource_id, thread_id=thread_id, stream=False)
    data = await http.post(path, json=_chat_body(message, model))
    return SkillChatResponseDto.model_validate(data)


def chat_stream_session(
    http: HttpClient,
    resource: str,
    resource_id: Union[int, str],
    message: str,
    *,
    model: str,
    thread_id: Optional[str] = None,
) -> ChatStream:
    validate_id(resource_id, name=f"{resource}_id")
    validate_chat_model(model)
    path = _chat_path(resource, resource_id, thread_id=thread_id, stream=True)
    return ChatStream(http, path, _chat_body(message, model))


def chat_stream_session_async(
    http: AsyncHttpClient,
    resource: str,
    resource_id: Union[int, str],
    message: str,
    *,
    model: str,
    thread_id: Optional[str] = None,
) -> AsyncChatStream:
    validate_id(resource_id, name=f"{resource}_id")
    validate_chat_model(model)
    path = _chat_path(resource, resource_id, thread_id=thread_id, stream=True)
    return AsyncChatStream(http, path, _chat_body(message, model))


def chat_via_stream(
    http: HttpClient,
    resource: str,
    resource_id: Union[int, str],
    message: str,
    *,
    model: str,
    thread_id: Optional[str] = None,
) -> ChatResult:
    """Buffered chat implemented by consuming the SSE stream until done."""
    with chat_stream_session(
        http, resource, resource_id, message, model=model, thread_id=thread_id
    ) as stream:
        for _ in stream.text_stream:
            pass
        return stream.get_final_result()


async def chat_via_stream_async(
    http: AsyncHttpClient,
    resource: str,
    resource_id: Union[int, str],
    message: str,
    *,
    model: str,
    thread_id: Optional[str] = None,
) -> ChatResult:
    async with chat_stream_session_async(
        http, resource, resource_id, message, model=model, thread_id=thread_id
    ) as stream:
        async for _ in stream.text_stream:
            pass
        return stream.get_final_result()
