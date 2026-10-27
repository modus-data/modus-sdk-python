"""Chat sessions: one turn streamed live from the agent host."""

from __future__ import annotations

from dataclasses import dataclass
from typing import (
    TYPE_CHECKING,
    Any,
    AsyncIterator,
    Dict,
    Generator,
    Iterator,
    List,
    Literal,
    Optional,
    Union,
)

from ._agent_run_request import resolve_agent_run_session_id
from ._config import ModusConfig, require_agent_host
from ._exceptions import ModusError, RunCancelledError, StreamTimeoutError
from ._http import AsyncHttpClient, HttpClient
from ._openapi_invoke import format_operation_path, path_segment
from ._streaming import parse_sse_stream
from ._validation import validate_chat_model, validate_id
from .types.chat import ChatResult
from .types.runs import (
    ApprovalRequiredEvent,
    AssistantContentResetEvent,
    CancelledEvent,
    DoneEvent,
    ErrorEvent,
    RunEvent,
    StreamTimeoutEvent,
    TokenEvent,
)

ChatTargetKind = Literal["scopes", "workflows", "modus"]
Decision = Literal["approve", "deny"]

_RUN_OPERATIONS = {
    "scopes": "ScopeRunsController_create",
    "workflows": "WorkflowRunsController_create",
}


@dataclass(frozen=True)
class _ChatRequest:
    path: str
    body: Dict[str, Any]
    session_id: str


def _effective_thread_id(thread_id: Optional[str]) -> Optional[str]:
    """Treat None and blank strings as "start a new thread"."""
    if thread_id is None or not thread_id.strip():
        return None
    return thread_id


def _raise_for_event(event: RunEvent) -> None:
    if isinstance(event, ErrorEvent):
        raise ModusError(event.message)
    if isinstance(event, CancelledEvent):
        raise RunCancelledError()
    if isinstance(event, StreamTimeoutEvent):
        raise StreamTimeoutError()


def _resume_request(final: ChatResult, decision: Decision) -> _ChatRequest:
    validate_id(final.run_id, name="run_id")
    return _ChatRequest(
        path=f"/agent/v1/runs/{path_segment(final.run_id)}/resume",
        body={"sessionId": final.thread_id, "decision": decision},
        session_id=final.thread_id,
    )


def _missing_attribute(session: object, name: str, migration: str) -> AttributeError:
    """chat() used to return the result itself; name the new spelling for its fields."""
    hint = f"; chat() returns a session now: use {migration.format(name)}" if name in ChatResult.model_fields else ""
    return AttributeError(f"{type(session).__name__!r} object has no attribute {name!r}{hint}")


def _last_top_level_reset(events: List[RunEvent]) -> int:
    """Index of the last top-level reset among cached events, or -1."""
    for index in range(len(events) - 1, -1, -1):
        event = events[index]
        if isinstance(event, AssistantContentResetEvent) and event.sub_agent is None:
            return index
    return -1


def _reply_text(index: int, event: RunEvent, last_reset: int) -> str:
    """The reply text an event adds; a reset replaces everything before it."""
    if index < last_reset:
        return ""
    if index == last_reset and isinstance(event, AssistantContentResetEvent):
        return event.content
    if isinstance(event, TokenEvent) and event.sub_agent is None:
        return event.content
    return ""


class _SessionState:
    """What a session has received so far, shared by the sync and async variants."""

    def __init__(self, request: _ChatRequest) -> None:
        self.request = request
        self.received: List[RunEvent] = []
        self.finished = False
        self.failure: Optional[BaseException] = None
        self.final: Optional[ChatResult] = None
        self.approval: Optional[ApprovalRequiredEvent] = None

    def body(self, reset_aware: bool) -> Dict[str, Any]:
        """The request body; a reset-aware consumer opts into protocol version 2."""
        if not reset_aware:
            return dict(self.request.body)
        return {**self.request.body, "streamProtocolVersion": 2}

    def accept(self, event: RunEvent) -> bool:
        """Record one event; returns True when it ends the run."""
        _raise_for_event(event)
        if isinstance(event, ApprovalRequiredEvent):
            self.approval = event
        if isinstance(event, DoneEvent):
            self.final = ChatResult(
                content=event.content or "",
                thread_id=event.thread_id or self.request.session_id,
                run_id=event.run_id,
                approval=self.approval,
            )
            return True
        return False

    def require_final(self) -> ChatResult:
        """The finished run's result; raises when the run has not finished."""
        if self.final is None:
            raise ModusError("Chat stream ended without a done event")
        return self.final


class ChatSession:
    """One chat turn, streamed live from the agent host.

    Iterate ``text_stream`` for the reply as it arrives, or call ``result()``
    for the final answer. The request is sent once: iterating again, or calling
    ``result()`` after iterating, replays what arrived.

    Example:
        >>> chat = client.scopes.chat(scope_id, "What is our ARR trend?", model="claude-sonnet-5.5")
        >>> for token in chat.text_stream:
        ...     print(token, end="")
        >>> thread_id = chat.result().thread_id
    """

    def __init__(self, http: HttpClient, request: _ChatRequest) -> None:
        self._http = http
        self._state = _SessionState(request)
        self._live: Optional[Generator[RunEvent, None, None]] = None

    def __enter__(self) -> "ChatSession":
        return self

    def __exit__(self, *args: object) -> None:
        self.close()

    if not TYPE_CHECKING:  # runtime only, so type checkers still flag a wrong attribute

        def __getattr__(self, name: str) -> Any:
            raise _missing_attribute(self, name, "chat.result().{}")

    def close(self) -> None:
        """Close the underlying stream if it is still open."""
        if self._live is not None:
            self._live.close()

    @property
    def text_stream(self) -> Iterator[str]:
        """The assistant's reply as text chunks, as they arrive. Sub-agent output is left out."""
        return self._text_stream()

    def _text_stream(self) -> Iterator[str]:
        # A replay of a protocol-2 stream can hold resets; text before the last one was replaced.
        # ponytail: a reset arriving live after text was yielded cannot be taken back.
        last_reset = _last_top_level_reset(self._state.received)
        for index, event in enumerate(self._replay(reset_aware=False)):
            text = _reply_text(index, event, last_reset)
            if text:
                yield text

    @property
    def event_stream(self) -> Iterator[RunEvent]:
        """Every run event (tokens, approvals, done, …) as it arrives."""
        return self._replay(reset_aware=True)

    def result(self) -> ChatResult:
        """Wait for the run to finish and return its final answer.

        ``approval`` is set when the run stopped for a decision; continue with
        ``resume``.

        Raises:
            ModusError: when the run reports an error or ends without finishing.
        """
        for _ in self._replay(reset_aware=True):
            pass
        return self._state.require_final()

    def resume(self, *, decision: Decision) -> "ChatSession":
        """Approve or deny the action this run stopped for, continuing the conversation.

        Args:
            decision: ``"approve"`` or ``"deny"``.

        Returns:
            A new session for the continued run.

        Raises:
            ModusError: when called before the run has finished.

        Example:
            >>> chat = client.modus.chat("Fix the typo in accounts", model="claude-sonnet-5.5")
            >>> if chat.result().approval:
            ...     print(chat.resume(decision="approve").result().content)
        """
        return ChatSession(self._http, _resume_request(self._state.require_final(), decision))

    # ponytail: one consumer at a time; concurrent iterators would race on _live.
    def _replay(self, *, reset_aware: bool) -> Iterator[RunEvent]:
        state = self._state
        index = 0
        while True:
            if index < len(state.received):
                index += 1
                yield state.received[index - 1]
                continue
            if state.failure is not None:
                raise state.failure
            if state.finished:
                return
            if self._live is None:
                self._live = self._open(reset_aware)
            try:
                state.received.append(next(self._live))
            except StopIteration:
                state.finished = True
            except Exception as error:
                state.failure = error
                raise
            if state.final is not None:
                # done is the last event: release the connection now, even if the consumer stops here.
                state.finished = True
                self.close()

    def _open(self, reset_aware: bool) -> Generator[RunEvent, None, None]:
        state = self._state
        for line in self._http.stream_post(state.request.path, json=state.body(reset_aware)):
            for event in parse_sse_stream(iter([line])):
                ends = state.accept(event)
                yield event
                if ends:
                    return


class AsyncChatSession:
    """Async variant of :class:`ChatSession`. ``await`` it for the final answer.

    Example:
        >>> result = await client.scopes.chat(scope_id, "What is our ARR trend?", model="claude-sonnet-5.5")
        >>> async with client.modus.chat("Summarize ARR", model="claude-sonnet-5.5") as chat:
        ...     async for token in chat.text_stream:
        ...         print(token, end="")
    """

    def __init__(self, http: AsyncHttpClient, request: _ChatRequest) -> None:
        self._http = http
        self._state = _SessionState(request)
        self._live: Optional[AsyncIterator[RunEvent]] = None

    async def __aenter__(self) -> "AsyncChatSession":
        return self

    async def __aexit__(self, *args: object) -> None:
        await self.aclose()

    if not TYPE_CHECKING:  # runtime only, so type checkers still flag a wrong attribute

        def __getattr__(self, name: str) -> Any:
            raise _missing_attribute(self, name, "(await chat).{}")

    def __await__(self) -> Generator[Any, None, ChatResult]:
        return self.result().__await__()

    async def aclose(self) -> None:
        """Close the underlying stream if it is still open."""
        if self._live is not None:
            await self._live.aclose()  # type: ignore[attr-defined]

    @property
    def text_stream(self) -> AsyncIterator[str]:
        """The assistant's reply as text chunks, as they arrive. Sub-agent output is left out."""
        return self._text_stream()

    async def _text_stream(self) -> AsyncIterator[str]:
        last_reset = _last_top_level_reset(self._state.received)
        index = 0
        async for event in self._replay(reset_aware=False):
            text = _reply_text(index, event, last_reset)
            index += 1
            if text:
                yield text

    @property
    def event_stream(self) -> AsyncIterator[RunEvent]:
        """Every run event (tokens, approvals, done, …) as it arrives."""
        return self._replay(reset_aware=True)

    async def result(self) -> ChatResult:
        """Wait for the run to finish and return its final answer. See :meth:`ChatSession.result`."""
        async for _ in self._replay(reset_aware=True):
            pass
        return self._state.require_final()

    def resume(self, *, decision: Decision) -> "AsyncChatSession":
        """Approve or deny the action this run stopped for. See :meth:`ChatSession.resume`."""
        return AsyncChatSession(self._http, _resume_request(self._state.require_final(), decision))

    async def _replay(self, *, reset_aware: bool) -> AsyncIterator[RunEvent]:
        state = self._state
        index = 0
        while True:
            if index < len(state.received):
                index += 1
                yield state.received[index - 1]
                continue
            if state.failure is not None:
                raise state.failure
            if state.finished:
                return
            if self._live is None:
                self._live = self._open(reset_aware)
            try:
                state.received.append(await self._live.__anext__())
            except StopAsyncIteration:
                state.finished = True
            except Exception as error:
                state.failure = error
                raise
            if state.final is not None:
                state.finished = True
                await self.aclose()

    async def _open(self, reset_aware: bool) -> AsyncIterator[RunEvent]:
        state = self._state
        lines = self._http.stream_post(state.request.path, json=state.body(reset_aware))
        try:
            async for line in lines:
                for event in parse_sse_stream(iter([line])):
                    ends = state.accept(event)
                    yield event
                    if ends:
                        return
        finally:
            # async for does not close its iterator; without this the HTTP stream stays open.
            await lines.aclose()  # type: ignore[attr-defined]


def _chat_request(
    config: ModusConfig,
    kind: ChatTargetKind,
    target_id: Optional[Union[int, str]],
    message: str,
    *,
    model: str,
    thread_id: Optional[str],
) -> _ChatRequest:
    if kind != "modus":
        validate_id(target_id, name=f"{kind[:-1]}_id")  # type: ignore[arg-type]
    validate_chat_model(model)
    require_agent_host(config)
    path = (
        "/agent/v1/modus/runs"
        if kind == "modus"
        else format_operation_path(_RUN_OPERATIONS[kind], {"id": target_id})
    )
    session_id = resolve_agent_run_session_id(_effective_thread_id(thread_id))
    body: Dict[str, Any] = {"message": message, "config": {"model": model}, "sessionId": session_id}
    if config.organization_id is not None:
        body["organizationId"] = config.organization_id
    return _ChatRequest(path=path, body=body, session_id=session_id)


def start_chat(
    http: HttpClient,
    config: ModusConfig,
    kind: ChatTargetKind,
    target_id: Optional[Union[int, str]],
    message: str,
    *,
    model: str,
    thread_id: Optional[str] = None,
) -> ChatSession:
    return ChatSession(
        http, _chat_request(config, kind, target_id, message, model=model, thread_id=thread_id)
    )


def start_chat_async(
    http: AsyncHttpClient,
    config: ModusConfig,
    kind: ChatTargetKind,
    target_id: Optional[Union[int, str]],
    message: str,
    *,
    model: str,
    thread_id: Optional[str] = None,
) -> AsyncChatSession:
    return AsyncChatSession(
        http, _chat_request(config, kind, target_id, message, model=model, thread_id=thread_id)
    )
