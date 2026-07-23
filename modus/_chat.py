"""Shared chat path building and SSE stream session helpers."""

from __future__ import annotations

from typing import Any, AsyncIterator, Dict, Iterator, List, Literal, Optional, Union
from urllib.parse import quote

from ._agent_run_request import resolve_agent_run_session_id
from ._exceptions import ModusError, RunCancelledError, StreamTimeoutError
from ._generated.models import SkillChatRequestDto, SkillChatResponseDto
from ._http import AsyncHttpClient, HttpClient
from ._openapi_invoke import format_operation_path
from ._streaming import parse_sse_stream
from ._validation import validate_chat_model, validate_id
from .types.chat import ChatResult
from .types.runs import (
    AssistantContentResetEvent,
    CancelledEvent,
    DoneEvent,
    ErrorEvent,
    RunEvent,
    StreamTimeoutEvent,
    TokenEvent,
)

RunVersion = Union[Literal["published", "draft"], str]


def _effective_thread_id(thread_id: Optional[str]) -> Optional[str]:
    """Treat None and blank strings as "start a new thread"."""
    if thread_id is None:
        return None
    if isinstance(thread_id, str) and not thread_id.strip():
        return None
    return thread_id


def _resolve_session_id(thread_id: Optional[str]) -> str:
    """Agent-host runs always require sessionId — reuse thread_id or mint a UUID."""
    return resolve_agent_run_session_id(_effective_thread_id(thread_id))


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


def _modus_chat_path(*, thread_id: Optional[str], stream: bool) -> str:
    suffix = "/stream" if stream else ""
    if thread_id is not None:
        validate_id(thread_id, name="thread_id")
    tid = _effective_thread_id(thread_id)
    if tid is not None:
        safe_tid = quote(str(tid), safe="")
        return f"/api/v1/modus/conversations/{safe_tid}/chat{suffix}"
    return f"/api/v1/modus/chat{suffix}"


def _chat_body(message: str, model: str) -> Dict[str, Any]:
    return SkillChatRequestDto(message=message, model=model).model_dump(  # type: ignore[arg-type]
        by_alias=True,
        exclude_none=True,
    )


# ---------------------------------------------------------------------------
# Agent-host runs paths (streaming only)
# ---------------------------------------------------------------------------


def _agent_host_modus_runs_path() -> str:
    """POST {agent_host}/agent/v1/modus/runs — SSE stream."""
    return "/agent/v1/modus/runs"


def _agent_runs_body(
    message: str,
    model: str,
    *,
    session_id: str,
    organization_id: Optional[str] = None,
    version: Optional[RunVersion] = None,
) -> Dict[str, Any]:
    """Build the request body for agent-host runs (streaming) requests.

    Args:
        message:          The user message.
        model:            Model id, e.g. ``"claude-sonnet-5"``.
        session_id:       Conversation/session ID (always required by agent-host).
        organization_id:  Optional Clerk org id; omit to let the server use the PAT org.
        version:          Run a specific variation — ``"published"`` or ``"draft"``.
    """
    body: Dict[str, Any] = {
        "message": message,
        "config": {"model": model},
        "sessionId": session_id,
    }
    if organization_id is not None:
        body["organizationId"] = organization_id
    if version is not None:
        body["version"] = version
    return body


def _org_from_http(http: Union[HttpClient, AsyncHttpClient]) -> Optional[str]:
    return getattr(http.config, "organization_id", None)


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
        for event in self._event_stream_impl(supports_reset=False):
            if isinstance(event, TokenEvent):
                yield event.content

    @property
    def event_stream(self) -> Iterator[RunEvent]:
        return self._event_stream_impl(supports_reset=True)

    def _event_stream_impl(self, *, supports_reset: bool) -> Iterator[RunEvent]:
        body = dict(self._body)
        if supports_reset:
            body["streamProtocolVersion"] = 2
        for line in self._http.stream_post(self._path, json=body):
            for event in parse_sse_stream(iter([line])):
                event = _raise_for_event(event)
                if isinstance(event, TokenEvent):
                    self._text_parts.append(event.content)
                if isinstance(event, AssistantContentResetEvent):
                    self._text_parts[:] = [event.content]
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
        async for event in self._event_stream_impl(supports_reset=False):
            if isinstance(event, TokenEvent):
                yield event.content

    @property
    def event_stream(self) -> AsyncIterator[RunEvent]:
        return self._event_stream_impl(supports_reset=True)

    async def _event_stream_impl(self, *, supports_reset: bool) -> AsyncIterator[RunEvent]:
        body = dict(self._body)
        if supports_reset:
            body["streamProtocolVersion"] = 2
        async for line in self._http.stream_post(self._path, json=body):
            for event in parse_sse_stream(iter([line])):
                event = _raise_for_event(event)
                if isinstance(event, TokenEvent):
                    self._text_parts.append(event.content)
                if isinstance(event, AssistantContentResetEvent):
                    self._text_parts[:] = [event.content]
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


def modus_chat_buffered(
    http: HttpClient,
    message: str,
    *,
    model: str,
    thread_id: Optional[str] = None,
) -> ChatResult:
    validate_chat_model(model)
    path = _modus_chat_path(thread_id=thread_id, stream=False)
    data = http.post(path, json=_chat_body(message, model))
    return SkillChatResponseDto.model_validate(data)


async def modus_chat_buffered_async(
    http: AsyncHttpClient,
    message: str,
    *,
    model: str,
    thread_id: Optional[str] = None,
) -> ChatResult:
    validate_chat_model(model)
    path = _modus_chat_path(thread_id=thread_id, stream=False)
    data = await http.post(path, json=_chat_body(message, model))
    return SkillChatResponseDto.model_validate(data)


# ---------------------------------------------------------------------------
# Agent-host stream sessions (scopes / modus / workflows)
#
# Scope and workflow run paths (/agent/v1/scopes|workflows/{id}/runs) are
# resolved from the generated OPERATIONS registry rather than a hardcoded
# literal; the Modus run path is a fixed agent-host route.
# ---------------------------------------------------------------------------


def modus_stream_session(
    agent_http: HttpClient,
    message: str,
    *,
    model: str,
    thread_id: Optional[str] = None,
) -> ChatStream:
    """Stream a Modus chat via the agent host's by-reference runs path."""
    validate_chat_model(model)
    path = _agent_host_modus_runs_path()
    body = _agent_runs_body(
        message,
        model,
        session_id=_resolve_session_id(thread_id),
        organization_id=_org_from_http(agent_http),
    )
    return ChatStream(agent_http, path, body)


def modus_stream_session_async(
    agent_http: AsyncHttpClient,
    message: str,
    *,
    model: str,
    thread_id: Optional[str] = None,
) -> AsyncChatStream:
    """Async stream a Modus chat via the agent host's by-reference runs path."""
    validate_chat_model(model)
    path = _agent_host_modus_runs_path()
    body = _agent_runs_body(
        message,
        model,
        session_id=_resolve_session_id(thread_id),
        organization_id=_org_from_http(agent_http),
    )
    return AsyncChatStream(agent_http, path, body)


def scope_stream_session(
    agent_http: HttpClient,
    resource_id: Union[int, str],
    message: str,
    *,
    model: str,
    thread_id: Optional[str] = None,
    version: Optional[RunVersion] = None,
) -> ChatStream:
    """Stream a scope chat via the agent host's by-reference runs path."""
    validate_id(resource_id, name="scope_id")
    validate_chat_model(model)
    path = format_operation_path("ScopeRunsController_create", {"id": resource_id})
    body = _agent_runs_body(
        message,
        model,
        session_id=_resolve_session_id(thread_id),
        organization_id=_org_from_http(agent_http),
        version=version,
    )
    return ChatStream(agent_http, path, body)


def scope_stream_session_async(
    agent_http: AsyncHttpClient,
    resource_id: Union[int, str],
    message: str,
    *,
    model: str,
    thread_id: Optional[str] = None,
    version: Optional[RunVersion] = None,
) -> AsyncChatStream:
    """Async stream a scope chat via the agent host's by-reference runs path."""
    validate_id(resource_id, name="scope_id")
    validate_chat_model(model)
    path = format_operation_path("ScopeRunsController_create", {"id": resource_id})
    body = _agent_runs_body(
        message,
        model,
        session_id=_resolve_session_id(thread_id),
        organization_id=_org_from_http(agent_http),
        version=version,
    )
    return AsyncChatStream(agent_http, path, body)


def workflow_stream_session(
    agent_http: HttpClient,
    resource_id: Union[int, str],
    message: str,
    *,
    model: str,
    thread_id: Optional[str] = None,
    version: Optional[RunVersion] = None,
) -> ChatStream:
    """Stream a workflow chat via the agent host's by-reference runs path."""
    validate_id(resource_id, name="workflow_id")
    validate_chat_model(model)
    path = format_operation_path("WorkflowRunsController_create", {"id": resource_id})
    body = _agent_runs_body(
        message,
        model,
        session_id=_resolve_session_id(thread_id),
        organization_id=_org_from_http(agent_http),
        version=version,
    )
    return ChatStream(agent_http, path, body)


def workflow_stream_session_async(
    agent_http: AsyncHttpClient,
    resource_id: Union[int, str],
    message: str,
    *,
    model: str,
    thread_id: Optional[str] = None,
    version: Optional[RunVersion] = None,
) -> AsyncChatStream:
    """Async stream a workflow chat via the agent host's by-reference runs path."""
    validate_id(resource_id, name="workflow_id")
    validate_chat_model(model)
    path = format_operation_path("WorkflowRunsController_create", {"id": resource_id})
    body = _agent_runs_body(
        message,
        model,
        session_id=_resolve_session_id(thread_id),
        organization_id=_org_from_http(agent_http),
        version=version,
    )
    return AsyncChatStream(agent_http, path, body)
