"""List and retrieve run history for a workflow."""
from __future__ import annotations

from dataclasses import dataclass
from typing import (
    Any,
    AsyncIterator,
    Dict,
    Iterator,
    List,
    Literal,
    Mapping,
    Optional,
    Sequence,
    Union,
)

from ..._config import ModusConfig
from ..._generated.models import (
    ActiveRunsBySessionResponseDto,
    ActiveRunsResponseDto,
    GetAutomationRunResponseDto,
    ListAutomationRunsResponseDto,
)
from ..._http import AsyncHttpClient, HttpClient
from ..._openapi_invoke import (
    invoke_operation,
    invoke_operation_async,
    invoke_operation_stream,
    invoke_operation_stream_async,
)
from ..._pagination import aip_list_params, normalize_page_token
from ..._retry import async_with_retry, with_retry
from ..._streaming import parse_sse_stream
from ..._validation import validate_id, validate_page_size
from ...types.agent_runs import ActiveConversationRun, AgentRun, AgentRunListItem
from ...types.pagination import AsyncPage, Page
from ...types.runs import RunEvent

# Documented filter values. These are hints, not a closed set: the server may
# accept additional values, so any string is allowed.
RunStatus = Union[
    Literal["running", "awaiting_human", "completed", "error", "cancelled", "all_executions"],
    str,
]
RunTimeframe = Union[Literal["last_hour", "last_day", "last_week"], str]
ApprovalScope = Union[Literal["mine", "all"], str]


@dataclass(frozen=True)
class RunOperations:
    """Which run operationIds the workflow runs resource calls.

    ``list``/``get`` are the modus-api history endpoints; ``create`` runs the
    parent workflow and ``create_scope`` runs a (subordinate) scope — both are
    agent-service streaming operations resolved from the registry.
    """

    list: str
    get: str
    active: str
    active_by_session: str
    create: str
    create_scope: str


WORKFLOW_RUN_OPERATIONS = RunOperations(
    list="WorkflowRunsController_list",
    get="WorkflowRunsController_get",
    active="RunLifecycleController_active",
    active_by_session="RunLifecycleController_activeBySession",
    create="WorkflowRunsController_create",
    create_scope="ScopeRunsController_create",
)


def _parse_run(raw: dict) -> AgentRun:
    return GetAutomationRunResponseDto.model_validate(raw)


def _dedupe_session_ids(session_ids: Sequence[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for session_id in session_ids:
        trimmed = str(session_id).strip()
        if not trimmed or trimmed in seen:
            continue
        seen.add(trimmed)
        result.append(trimmed)
    if len(result) > 100:
        raise ValueError("session_ids must contain at most 100 ids")
    return result


def _runs_list_params(
    page_size: int,
    page_token: Optional[str],
    status: Optional[RunStatus],
    timeframe: Optional[RunTimeframe],
    approval_scope: Optional[ApprovalScope],
    search: Optional[str],
) -> Dict[str, Any]:
    params: Dict[str, Any] = {"pageSize": page_size}
    if page_token:
        params["pageToken"] = page_token
    if status is not None:
        params["status"] = status
    if timeframe is not None:
        params["timeframe"] = timeframe
    if approval_scope is not None:
        params["approvalScope"] = approval_scope
    if search is not None:
        params["search"] = search
    return params


def _request_body(body: Mapping[str, Any]) -> Dict[str, Any]:
    return dict(body)


def _optional_body(body: Optional[Mapping[str, Any]]) -> Dict[str, Any]:
    return dict(body or {})


def _parse_events(lines: Iterator[str]) -> Iterator[RunEvent]:
    yield from parse_sse_stream(lines)


async def _parse_events_async(lines: AsyncIterator[str]) -> AsyncIterator[RunEvent]:
    async for line in lines:
        for event in parse_sse_stream(iter([line])):
            yield event


class WorkflowRunsResource:
    def __init__(
        self,
        http: HttpClient,
        config: ModusConfig,
        ops: RunOperations = WORKFLOW_RUN_OPERATIONS,
    ) -> None:
        self._http = http
        self._config = config
        self._ops = ops

    def list(
        self,
        workflow_id: Union[int, str],
        *,
        page_size: int = 25,
        page_token: Optional[str] = None,
        status: Optional[RunStatus] = None,
        timeframe: Optional[RunTimeframe] = None,
        approval_scope: Optional[ApprovalScope] = None,
        search: Optional[str] = None,
    ) -> Page[AgentRunListItem]:
        """
        List runs for a workflow.

        Args:
            workflow_id:     Workflow ID or slug.
            page_size:       Maximum number of items to return (default 25, max 100).
            page_token:      Token from a previous page's ``next_page_token``; omit for the first page.
            status:          Filter by run status (e.g. ``"running"``, ``"awaiting_human"``,
                             ``"completed"``, ``"error"``, ``"cancelled"``, ``"all_executions"``).
            timeframe:       Filter by time window (e.g. ``"last_hour"``, ``"last_day"``, ``"last_week"``).
            approval_scope:  When ``status="awaiting_human"``, scope to ``"mine"`` or ``"all"``.
            search:          Free-text search filter.
        """
        validate_id(workflow_id, name="workflow_id")
        validate_page_size(page_size, max_page_size=100)
        return self._list_page(
            workflow_id,
            page_size=page_size,
            page_token=page_token,
            status=status,
            timeframe=timeframe,
            approval_scope=approval_scope,
            search=search,
        )

    def _list_page(
        self,
        workflow_id: Union[int, str],
        *,
        page_size: int,
        page_token: Optional[str],
        status: Optional[RunStatus],
        timeframe: Optional[RunTimeframe],
        approval_scope: Optional[ApprovalScope],
        search: Optional[str],
    ) -> Page[AgentRunListItem]:
        params = _runs_list_params(
            page_size, page_token, status, timeframe, approval_scope, search
        )
        data = with_retry(
            lambda: invoke_operation(
                self._http,
                self._ops.list,
                path_params={"id": workflow_id},
                query=params,
            ),
            self._config.max_retries,
        )
        wire = ListAutomationRunsResponseDto.model_validate(data)
        items = list(wire.runs)
        next_page_token = normalize_page_token(wire.next_page_token)
        return Page(
            items=items,
            next_page_token=next_page_token,
            _fetch_page=lambda tok: self._list_page(
                workflow_id,
                page_size=page_size,
                page_token=tok,
                status=status,
                timeframe=timeframe,
                approval_scope=approval_scope,
                search=search,
            ),
        )

    def active(
        self,
        *,
        page_size: int = 50,
        page_token: Optional[str] = None,
    ) -> Page[ActiveConversationRun]:
        """
        List active conversation runs for the current user.

        Args:
            page_size:  Maximum number of active runs to return (default 50, max 100).
            page_token: Token from a previous page's ``next_page_token``; omit for the first page.
        """
        validate_page_size(page_size, max_page_size=100)
        return self._active_page(page_size=page_size, page_token=page_token)

    def _active_page(
        self,
        *,
        page_size: int,
        page_token: Optional[str],
    ) -> Page[ActiveConversationRun]:
        data = with_retry(
            lambda: invoke_operation(
                self._http,
                self._ops.active,
                query=aip_list_params(page_size, page_token),
            ),
            self._config.max_retries,
        )
        wire = ActiveRunsResponseDto.model_validate(data)
        return Page(
            items=list(wire.runs),
            next_page_token=normalize_page_token(wire.next_page_token),
            _fetch_page=lambda tok: self._active_page(
                page_size=page_size,
                page_token=tok,
            ),
        )

    def active_by_session(self, session_ids: Sequence[str]) -> List[ActiveConversationRun]:
        """
        Return active runs for the supplied conversation thread ids.

        Args:
            session_ids: Conversation thread ids to check; blanks and duplicates are ignored.
        """
        ids = _dedupe_session_ids(session_ids)
        data = with_retry(
            lambda: invoke_operation(
                self._http,
                self._ops.active_by_session,
                json_body={"sessionIds": ids},
            ),
            self._config.max_retries,
        )
        return list(ActiveRunsBySessionResponseDto.model_validate(data).runs)

    def get(
        self,
        workflow_id: Union[int, str],
        run_id: str,
        *,
        temporal_run_id: Optional[str] = None,
    ) -> AgentRun:
        """
        Retrieve a Modus workflow run by ID.

        Args:
            workflow_id:      Modus workflow ID or slug.
            run_id:           Run ID.
            temporal_run_id:  Optional Temporal run ID when disambiguating.
        """
        validate_id(workflow_id, name="workflow_id")
        if not run_id or not str(run_id).strip():
            raise ValueError("run_id must be a non-empty string")
        query: Dict[str, Any] = {}
        if temporal_run_id is not None:
            query["temporalRunId"] = temporal_run_id
        data = with_retry(
            lambda: invoke_operation(
                self._http,
                self._ops.get,
                path_params={"id": workflow_id, "runId": run_id},
                query=query or None,
            ),
            self._config.max_retries,
        )
        return _parse_run(data)

    def create(
        self,
        workflow_id: Union[int, str],
        body: Mapping[str, Any],
    ) -> Iterator[RunEvent]:
        """
        Start a workflow run and stream its events.

        Args:
            workflow_id: Workflow ID or slug.
            body:        Run request fields such as message, sessionId, config, and runId.
        """
        validate_id(workflow_id, name="workflow_id")
        return _parse_events(
            invoke_operation_stream(
                self._http,
                self._ops.create,
                path_params={"id": workflow_id},
                json_body=_request_body(body),
            )
        )

    def create_scope(
        self,
        scope_id: Union[int, str],
        body: Mapping[str, Any],
    ) -> Iterator[RunEvent]:
        """
        Start a scope run and stream its events.

        Args:
            scope_id: Scope ID or slug.
            body:     Run request fields such as message, sessionId, config, and runId.
        """
        validate_id(scope_id, name="scope_id")
        return _parse_events(
            invoke_operation_stream(
                self._http,
                self._ops.create_scope,
                path_params={"id": scope_id},
                json_body=_request_body(body),
            )
        )

    def create_modus(self, body: Mapping[str, Any]) -> Iterator[RunEvent]:
        """
        Start a Modus run and stream its events.

        Args:
            body: Run request fields such as message, sessionId, config, and runId.
        """
        return _parse_events(
            invoke_operation_stream(
                self._http,
                "ModusRunsController_create",
                json_body=_request_body(body),
            )
        )

    def resume(self, run_id: str, body: Mapping[str, Any]) -> Iterator[RunEvent]:
        """
        Resume a paused run and stream its events.

        Args:
            run_id: Run ID to resume.
            body:   Resume request fields including the decision and message.
        """
        validate_id(run_id, name="run_id")
        return _parse_events(
            invoke_operation_stream(
                self._http,
                "ResumeRunsController_create",
                path_params={"runId": run_id},
                json_body=_request_body(body),
            )
        )

    def cancel(self, run_id: str, body: Optional[Mapping[str, Any]] = None) -> None:
        """
        Cancel a run.

        Args:
            run_id: Run ID to cancel.
            body:   Optional cancellation details.
        """
        validate_id(run_id, name="run_id")
        with_retry(
            lambda: invoke_operation(
                self._http,
                "RunLifecycleController_cancel",
                path_params={"runId": run_id},
                json_body=_optional_body(body),
            ),
            self._config.max_retries,
        )

    def interrupt(self, run_id: str, body: Optional[Mapping[str, Any]] = None) -> None:
        """
        Interrupt a run.

        Args:
            run_id: Run ID to interrupt.
            body:   Optional interruption details.
        """
        validate_id(run_id, name="run_id")
        with_retry(
            lambda: invoke_operation(
                self._http,
                "RunLifecycleController_interrupt",
                path_params={"runId": run_id},
                json_body=_optional_body(body),
            ),
            self._config.max_retries,
        )

    def edit_queued(self, run_id: str, body: Optional[Mapping[str, Any]] = None) -> None:
        """
        Edit a queued run.

        Args:
            run_id: Run ID to edit.
            body:   Optional queued-run edit details.
        """
        validate_id(run_id, name="run_id")
        with_retry(
            lambda: invoke_operation(
                self._http,
                "RunLifecycleController_editQueued",
                path_params={"runId": run_id},
                json_body=_optional_body(body),
            ),
            self._config.max_retries,
        )

    def events(self, run_id: str) -> Iterator[RunEvent]:
        """
        Stream run lifecycle events.

        Args:
            run_id: Run ID to follow.
        """
        validate_id(run_id, name="run_id")
        return _parse_events(
            invoke_operation_stream(
                self._http,
                "RunLifecycleController_events",
                path_params={"runId": run_id},
            )
        )

    def stream(self, run_id: str) -> Iterator[RunEvent]:
        """
        Stream run output events.

        Args:
            run_id: Run ID to follow.
        """
        validate_id(run_id, name="run_id")
        return _parse_events(
            invoke_operation_stream(
                self._http,
                "RunLifecycleController_stream",
                path_params={"runId": run_id},
            )
        )


class AsyncWorkflowRunsResource:
    def __init__(
        self,
        http: AsyncHttpClient,
        config: ModusConfig,
        ops: RunOperations = WORKFLOW_RUN_OPERATIONS,
    ) -> None:
        self._http = http
        self._config = config
        self._ops = ops

    async def list(
        self,
        workflow_id: Union[int, str],
        *,
        page_size: int = 25,
        page_token: Optional[str] = None,
        status: Optional[RunStatus] = None,
        timeframe: Optional[RunTimeframe] = None,
        approval_scope: Optional[ApprovalScope] = None,
        search: Optional[str] = None,
    ) -> AsyncPage[AgentRunListItem]:
        """
        List runs for a workflow.

        Args:
            workflow_id:     Workflow ID or slug.
            page_size:       Maximum number of items to return (default 25, max 100).
            page_token:      Token from a previous page's ``next_page_token``; omit for the first page.
            status:          Filter by run status (e.g. ``"running"``, ``"awaiting_human"``,
                             ``"completed"``, ``"error"``, ``"cancelled"``, ``"all_executions"``).
            timeframe:       Filter by time window (e.g. ``"last_hour"``, ``"last_day"``, ``"last_week"``).
            approval_scope:  When ``status="awaiting_human"``, scope to ``"mine"`` or ``"all"``.
            search:          Free-text search filter.
        """
        validate_id(workflow_id, name="workflow_id")
        validate_page_size(page_size, max_page_size=100)
        return await self._list_page(
            workflow_id,
            page_size=page_size,
            page_token=page_token,
            status=status,
            timeframe=timeframe,
            approval_scope=approval_scope,
            search=search,
        )

    async def _list_page(
        self,
        workflow_id: Union[int, str],
        *,
        page_size: int,
        page_token: Optional[str],
        status: Optional[RunStatus],
        timeframe: Optional[RunTimeframe],
        approval_scope: Optional[ApprovalScope],
        search: Optional[str],
    ) -> AsyncPage[AgentRunListItem]:
        params = _runs_list_params(
            page_size, page_token, status, timeframe, approval_scope, search
        )
        data = await async_with_retry(
            lambda: invoke_operation_async(
                self._http,
                self._ops.list,
                path_params={"id": workflow_id},
                query=params,
            ),
            self._config.max_retries,
        )
        wire = ListAutomationRunsResponseDto.model_validate(data)
        items = list(wire.runs)
        next_page_token = normalize_page_token(wire.next_page_token)
        return AsyncPage(
            items=items,
            next_page_token=next_page_token,
            _fetch_page=lambda tok: self._list_page(
                workflow_id,
                page_size=page_size,
                page_token=tok,
                status=status,
                timeframe=timeframe,
                approval_scope=approval_scope,
                search=search,
            ),
        )

    async def active(
        self,
        *,
        page_size: int = 50,
        page_token: Optional[str] = None,
    ) -> AsyncPage[ActiveConversationRun]:
        """
        List active conversation runs for the current user.

        Args:
            page_size:  Maximum number of active runs to return (default 50, max 100).
            page_token: Token from a previous page's ``next_page_token``; omit for the first page.
        """
        validate_page_size(page_size, max_page_size=100)
        return await self._active_page(page_size=page_size, page_token=page_token)

    async def _active_page(
        self,
        *,
        page_size: int,
        page_token: Optional[str],
    ) -> AsyncPage[ActiveConversationRun]:
        data = await async_with_retry(
            lambda: invoke_operation_async(
                self._http,
                self._ops.active,
                query=aip_list_params(page_size, page_token),
            ),
            self._config.max_retries,
        )
        wire = ActiveRunsResponseDto.model_validate(data)
        return AsyncPage(
            items=list(wire.runs),
            next_page_token=normalize_page_token(wire.next_page_token),
            _fetch_page=lambda tok: self._active_page(
                page_size=page_size,
                page_token=tok,
            ),
        )

    async def active_by_session(
        self,
        session_ids: Sequence[str],
    ) -> List[ActiveConversationRun]:
        """
        Return active runs for the supplied conversation thread ids.

        Args:
            session_ids: Conversation thread ids to check; blanks and duplicates are ignored.
        """
        ids = _dedupe_session_ids(session_ids)
        data = await async_with_retry(
            lambda: invoke_operation_async(
                self._http,
                self._ops.active_by_session,
                json_body={"sessionIds": ids},
            ),
            self._config.max_retries,
        )
        return list(ActiveRunsBySessionResponseDto.model_validate(data).runs)

    async def get(
        self,
        workflow_id: Union[int, str],
        run_id: str,
        *,
        temporal_run_id: Optional[str] = None,
    ) -> AgentRun:
        """
        Retrieve a Modus workflow run by ID.

        Args:
            workflow_id:      Modus workflow ID or slug.
            run_id:           Run ID.
            temporal_run_id:  Optional Temporal run ID when disambiguating.
        """
        validate_id(workflow_id, name="workflow_id")
        if not run_id or not str(run_id).strip():
            raise ValueError("run_id must be a non-empty string")
        query: Dict[str, Any] = {}
        if temporal_run_id is not None:
            query["temporalRunId"] = temporal_run_id
        data = await async_with_retry(
            lambda: invoke_operation_async(
                self._http,
                self._ops.get,
                path_params={"id": workflow_id, "runId": run_id},
                query=query or None,
            ),
            self._config.max_retries,
        )
        return _parse_run(data)

    async def create(
        self,
        workflow_id: Union[int, str],
        body: Mapping[str, Any],
    ) -> AsyncIterator[RunEvent]:
        """
        Start a workflow run and stream its events.

        Args:
            workflow_id: Workflow ID or slug.
            body:        Run request fields such as message, sessionId, config, and runId.
        """
        validate_id(workflow_id, name="workflow_id")
        async for event in _parse_events_async(
            invoke_operation_stream_async(
                self._http,
                self._ops.create,
                path_params={"id": workflow_id},
                json_body=_request_body(body),
            )
        ):
            yield event

    async def create_scope(
        self,
        scope_id: Union[int, str],
        body: Mapping[str, Any],
    ) -> AsyncIterator[RunEvent]:
        """
        Start a scope run and stream its events.

        Args:
            scope_id: Scope ID or slug.
            body:     Run request fields such as message, sessionId, config, and runId.
        """
        validate_id(scope_id, name="scope_id")
        async for event in _parse_events_async(
            invoke_operation_stream_async(
                self._http,
                self._ops.create_scope,
                path_params={"id": scope_id},
                json_body=_request_body(body),
            )
        ):
            yield event

    async def create_modus(self, body: Mapping[str, Any]) -> AsyncIterator[RunEvent]:
        """
        Start a Modus run and stream its events.

        Args:
            body: Run request fields such as message, sessionId, config, and runId.
        """
        async for event in _parse_events_async(
            invoke_operation_stream_async(
                self._http,
                "ModusRunsController_create",
                json_body=_request_body(body),
            )
        ):
            yield event

    async def resume(self, run_id: str, body: Mapping[str, Any]) -> AsyncIterator[RunEvent]:
        """
        Resume a paused run and stream its events.

        Args:
            run_id: Run ID to resume.
            body:   Resume request fields including the decision and message.
        """
        validate_id(run_id, name="run_id")
        async for event in _parse_events_async(
            invoke_operation_stream_async(
                self._http,
                "ResumeRunsController_create",
                path_params={"runId": run_id},
                json_body=_request_body(body),
            )
        ):
            yield event

    async def cancel(self, run_id: str, body: Optional[Mapping[str, Any]] = None) -> None:
        """
        Cancel a run.

        Args:
            run_id: Run ID to cancel.
            body:   Optional cancellation details.
        """
        validate_id(run_id, name="run_id")
        await async_with_retry(
            lambda: invoke_operation_async(
                self._http,
                "RunLifecycleController_cancel",
                path_params={"runId": run_id},
                json_body=_optional_body(body),
            ),
            self._config.max_retries,
        )

    async def interrupt(self, run_id: str, body: Optional[Mapping[str, Any]] = None) -> None:
        """
        Interrupt a run.

        Args:
            run_id: Run ID to interrupt.
            body:   Optional interruption details.
        """
        validate_id(run_id, name="run_id")
        await async_with_retry(
            lambda: invoke_operation_async(
                self._http,
                "RunLifecycleController_interrupt",
                path_params={"runId": run_id},
                json_body=_optional_body(body),
            ),
            self._config.max_retries,
        )

    async def edit_queued(
        self,
        run_id: str,
        body: Optional[Mapping[str, Any]] = None,
    ) -> None:
        """
        Edit a queued run.

        Args:
            run_id: Run ID to edit.
            body:   Optional queued-run edit details.
        """
        validate_id(run_id, name="run_id")
        await async_with_retry(
            lambda: invoke_operation_async(
                self._http,
                "RunLifecycleController_editQueued",
                path_params={"runId": run_id},
                json_body=_optional_body(body),
            ),
            self._config.max_retries,
        )

    async def events(self, run_id: str) -> AsyncIterator[RunEvent]:
        """
        Stream run lifecycle events.

        Args:
            run_id: Run ID to follow.
        """
        validate_id(run_id, name="run_id")
        async for event in _parse_events_async(
            invoke_operation_stream_async(
                self._http,
                "RunLifecycleController_events",
                path_params={"runId": run_id},
            )
        ):
            yield event

    async def stream(self, run_id: str) -> AsyncIterator[RunEvent]:
        """
        Stream run output events.

        Args:
            run_id: Run ID to follow.
        """
        validate_id(run_id, name="run_id")
        async for event in _parse_events_async(
            invoke_operation_stream_async(
                self._http,
                "RunLifecycleController_stream",
                path_params={"runId": run_id},
            )
        ):
            yield event
