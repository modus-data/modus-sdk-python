"""Agent runs — GET /api/v1/agents/{id}/runs."""
from __future__ import annotations

from typing import Any, Dict, Literal, Optional, Union
from urllib.parse import quote

from ..._config import ModusConfig
from ..._http import AsyncHttpClient, HttpClient
from ..._pagination import normalize_page_token
from ..._retry import async_with_retry, with_retry
from ..._validation import validate_id, validate_page_size
from ..._wire.agent_runs import (
    _AutomationRunListItemWire,
    _GetAutomationRunResponseWire,
    _ListAutomationRunsResponseWire,
)
from ...types.agent_runs import AgentRun, AgentRunListItem
from ...types.json_blob import JsonObject
from ...types.pagination import AsyncPage, Page

# Documented filter values. These are hints, not a closed set: the server may
# accept additional values, so any string is allowed.
RunStatus = Union[
    Literal["running", "awaiting_human", "completed", "error", "cancelled", "all_executions"],
    str,
]
RunTimeframe = Union[Literal["last_hour", "last_day", "last_week"], str]
ApprovalScope = Union[Literal["mine", "all"], str]


def _translate_run_item(wire: _AutomationRunListItemWire) -> AgentRunListItem:
    return AgentRunListItem(
        id=wire.id,
        workflow_id=wire.workflow_id,
        temporal_run_id=wire.temporal_run_id,
        agent_id=wire.agent_id,
        agent_name=wire.agent_name,
        agent_type=wire.agent_type,
        status=wire.status,
        trigger_type=wire.trigger_type,
        started_at=wire.started_at,
        ended_at=wire.ended_at,
        duration_ms=wire.duration_ms,
        summary=wire.summary,
        pending_approval=(
            JsonObject.model_validate(wire.pending_approval)
            if wire.pending_approval is not None
            else None
        ),
    )


class AgentRunsResource:
    def __init__(self, http: HttpClient, config: ModusConfig) -> None:
        self._http = http
        self._config = config

    def list(
        self,
        agent_id: Union[int, str],
        *,
        page_size: int = 25,
        page_token: Optional[str] = None,
        status: Optional[RunStatus] = None,
        timeframe: Optional[RunTimeframe] = None,
        approval_scope: Optional[ApprovalScope] = None,
        search: Optional[str] = None,
    ) -> Page[AgentRunListItem]:
        """
        List automation runs for an agent.

        Args:
            agent_id:        Agent ID or slug.
            page_size:       Maximum number of items to return (default 25, max 100).
            page_token:      Token from a previous page's ``next_page_token``; omit for the first page.
            status:          Filter by run status (e.g. ``"running"``, ``"awaiting_human"``,
                             ``"completed"``, ``"error"``, ``"cancelled"``, ``"all_executions"``).
            timeframe:       Filter by time window (e.g. ``"last_hour"``, ``"last_day"``, ``"last_week"``).
            approval_scope:  When ``status="awaiting_human"``, scope to ``"mine"`` or ``"all"``.
            search:          Free-text search filter.
        """
        validate_id(agent_id, name="agent_id")
        validate_page_size(page_size, max_page_size=100)
        return self._list_page(
            agent_id,
            page_size=page_size,
            page_token=page_token,
            status=status,
            timeframe=timeframe,
            approval_scope=approval_scope,
            search=search,
        )

    def _list_page(
        self,
        agent_id: Union[int, str],
        *,
        page_size: int,
        page_token: Optional[str],
        status: Optional[RunStatus],
        timeframe: Optional[RunTimeframe],
        approval_scope: Optional[ApprovalScope],
        search: Optional[str],
    ) -> Page[AgentRunListItem]:
        safe_id = quote(str(agent_id), safe="")
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

        data = with_retry(
            lambda: self._http.get(f"/api/v1/agents/{safe_id}/runs", params=params),
            self._config.max_retries,
        )
        wire = _ListAutomationRunsResponseWire.model_validate(data)
        items = [_translate_run_item(r) for r in wire.runs]
        next_page_token = normalize_page_token(wire.next_page_token)
        return Page(
            items=items,
            next_page_token=next_page_token,
            _fetch_page=lambda tok: self._list_page(
                agent_id,
                page_size=page_size,
                page_token=tok,
                status=status,
                timeframe=timeframe,
                approval_scope=approval_scope,
                search=search,
            ),
        )

    def get(
        self,
        agent_id: Union[int, str],
        run_id: str,
        *,
        temporal_run_id: Optional[str] = None,
    ) -> AgentRun:
        """
        Retrieve a Modus automation run by ID.

        Args:
            agent_id:         Modus agent ID or slug.
            run_id:           Automation run ID.
            temporal_run_id:  Optional Temporal run ID when disambiguating.
        """
        validate_id(agent_id, name="agent_id")
        if not run_id or not str(run_id).strip():
            raise ValueError("run_id must be a non-empty string")
        safe_id = quote(str(agent_id), safe="")
        safe_run = quote(str(run_id), safe="")
        params: Dict[str, Any] = {}
        if temporal_run_id is not None:
            params["temporalRunId"] = temporal_run_id
        data = with_retry(
            lambda: self._http.get(
                f"/api/v1/agents/{safe_id}/runs/{safe_run}",
                params=params or None,
            ),
            self._config.max_retries,
        )
        wire = _GetAutomationRunResponseWire.model_validate(data)
        return AgentRun(
            id=wire.id,
            workflow_id=wire.workflow_id,
            temporal_run_id=wire.temporal_run_id,
            agent_id=wire.agent_id,
            agent_name=wire.agent_name,
            agent_type=wire.agent_type,
            status=wire.status,
            started_at=wire.started_at,
            ended_at=wire.ended_at,
            history=(
                [JsonObject.model_validate(item) for item in wire.history]
                if wire.history is not None
                else None
            ),
        )


class AsyncAgentRunsResource:
    def __init__(self, http: AsyncHttpClient, config: ModusConfig) -> None:
        self._http = http
        self._config = config

    async def list(
        self,
        agent_id: Union[int, str],
        *,
        page_size: int = 25,
        page_token: Optional[str] = None,
        status: Optional[RunStatus] = None,
        timeframe: Optional[RunTimeframe] = None,
        approval_scope: Optional[ApprovalScope] = None,
        search: Optional[str] = None,
    ) -> AsyncPage[AgentRunListItem]:
        """
        List automation runs for an agent.

        Args:
            agent_id:        Agent ID or slug.
            page_size:       Maximum number of items to return (default 25, max 100).
            page_token:      Token from a previous page's ``next_page_token``; omit for the first page.
            status:          Filter by run status (e.g. ``"running"``, ``"awaiting_human"``,
                             ``"completed"``, ``"error"``, ``"cancelled"``, ``"all_executions"``).
            timeframe:       Filter by time window (e.g. ``"last_hour"``, ``"last_day"``, ``"last_week"``).
            approval_scope:  When ``status="awaiting_human"``, scope to ``"mine"`` or ``"all"``.
            search:          Free-text search filter.
        """
        validate_id(agent_id, name="agent_id")
        validate_page_size(page_size, max_page_size=100)
        return await self._list_page(
            agent_id,
            page_size=page_size,
            page_token=page_token,
            status=status,
            timeframe=timeframe,
            approval_scope=approval_scope,
            search=search,
        )

    async def _list_page(
        self,
        agent_id: Union[int, str],
        *,
        page_size: int,
        page_token: Optional[str],
        status: Optional[RunStatus],
        timeframe: Optional[RunTimeframe],
        approval_scope: Optional[ApprovalScope],
        search: Optional[str],
    ) -> AsyncPage[AgentRunListItem]:
        safe_id = quote(str(agent_id), safe="")
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

        data = await async_with_retry(
            lambda: self._http.get(f"/api/v1/agents/{safe_id}/runs", params=params),
            self._config.max_retries,
        )
        wire = _ListAutomationRunsResponseWire.model_validate(data)
        items = [_translate_run_item(r) for r in wire.runs]
        next_page_token = normalize_page_token(wire.next_page_token)
        return AsyncPage(
            items=items,
            next_page_token=next_page_token,
            _fetch_page=lambda tok: self._list_page(
                agent_id,
                page_size=page_size,
                page_token=tok,
                status=status,
                timeframe=timeframe,
                approval_scope=approval_scope,
                search=search,
            ),
        )

    async def get(
        self,
        agent_id: Union[int, str],
        run_id: str,
        *,
        temporal_run_id: Optional[str] = None,
    ) -> AgentRun:
        """
        Retrieve a Modus automation run by ID.

        Args:
            agent_id:         Modus agent ID or slug.
            run_id:           Automation run ID.
            temporal_run_id:  Optional Temporal run ID when disambiguating.
        """
        validate_id(agent_id, name="agent_id")
        if not run_id or not str(run_id).strip():
            raise ValueError("run_id must be a non-empty string")
        safe_id = quote(str(agent_id), safe="")
        safe_run = quote(str(run_id), safe="")
        params: Dict[str, Any] = {}
        if temporal_run_id is not None:
            params["temporalRunId"] = temporal_run_id
        data = await async_with_retry(
            lambda: self._http.get(
                f"/api/v1/agents/{safe_id}/runs/{safe_run}",
                params=params or None,
            ),
            self._config.max_retries,
        )
        wire = _GetAutomationRunResponseWire.model_validate(data)
        return AgentRun(
            id=wire.id,
            workflow_id=wire.workflow_id,
            temporal_run_id=wire.temporal_run_id,
            agent_id=wire.agent_id,
            agent_name=wire.agent_name,
            agent_type=wire.agent_type,
            status=wire.status,
            started_at=wire.started_at,
            ended_at=wire.ended_at,
            history=(
                [JsonObject.model_validate(item) for item in wire.history]
                if wire.history is not None
                else None
            ),
        )
