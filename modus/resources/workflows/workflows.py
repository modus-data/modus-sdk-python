"""Read-only workflows resource for the consumption client."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Optional, Union

from ..._chat import (
    AsyncChatStream,
    ChatStream,
    RunVersion,
    workflow_stream_session,
    workflow_stream_session_async,
)
from ..._config import ModusConfig
from ..._generated.models import AgentDto
from ..._http import AsyncHttpClient, HttpClient
from ..._openapi_invoke import invoke_operation, invoke_operation_async
from ..._pagination import (
    aip_list_params,
    build_aip_page_mapped,
    build_async_aip_page_mapped,
)
from ..._retry import async_with_retry, with_retry
from ..._validation import validate_id, validate_page_size
from ...types.agents import Agent, AgentType
from ...types.pagination import AsyncPage, Page
from ...types.views import VariationView
from .runs import (
    WORKFLOW_RUN_OPERATIONS,
    AsyncWorkflowRunsResource,
    RunOperations,
    WorkflowRunsResource,
)
from .workflow_actions import (
    AgentWorkflowActionsResource,
    AsyncAgentWorkflowActionsResource,
)


@dataclass(frozen=True)
class WorkflowsOperations:
    """Which operationIds the consumption workflows resource calls."""

    list: str
    get: str
    runs: RunOperations
    stream_session: Callable[..., ChatStream]
    stream_session_async: Callable[..., AsyncChatStream]


WORKFLOW_OPERATIONS = WorkflowsOperations(
    list="WorkflowsController_list",
    get="WorkflowsController_get",
    runs=WORKFLOW_RUN_OPERATIONS,
    stream_session=workflow_stream_session,
    stream_session_async=workflow_stream_session_async,
)


def _parse_workflow(raw: dict) -> Agent:
    return AgentDto.model_validate(raw)


def _workflows_list_params(
    page_size: int,
    page_token: Optional[str],
    search: Optional[str],
    type: Optional[AgentType],
    view: Optional[VariationView],
    include_variation: Optional[bool],
) -> dict:
    extra: dict = {}
    if search is not None:
        extra["search"] = search
    if type is not None:
        extra["type"] = type
    if view is not None:
        extra["view"] = view
    if include_variation is not None:
        extra["includeVariation"] = include_variation
    return aip_list_params(page_size, page_token, **extra)


class WorkflowsResource:
    """
    Read access to Modus workflows.

    client.workflows.list() → Page[Agent]
    client.workflows.get(workflow_id) → Agent

    To create, update, or deploy workflows use modus.management.ModusManagement.
    """

    def __init__(
        self,
        http: HttpClient,
        agent_http: HttpClient,
        config: ModusConfig,
        ops: WorkflowsOperations = WORKFLOW_OPERATIONS,
    ) -> None:
        self._http = http
        self._agent_http = agent_http
        self._config = config
        self._ops = ops
        self.runs = WorkflowRunsResource(http, config, ops.runs)
        self.workflow_actions = AgentWorkflowActionsResource(http, config)

    def list(
        self,
        *,
        page_size: int = 25,
        page_token: Optional[str] = None,
        search: Optional[str] = None,
        type: Optional[AgentType] = None,
        view: Optional[VariationView] = None,
        include_variation: Optional[bool] = None,
    ) -> Page[Agent]:
        """
        List workflows in the organisation.

        Args:
            page_size:         Items per page (default 25).
            page_token:        Opaque token from a previous page's ``next_page_token``.
            search:            Case-insensitive substring filter on the workflow name.
            type:              Filter by workflow type: ``"task"`` or ``"workflow"``.
            view:              Variation view — ``"active"`` (deployed) or ``"draft"``.
            include_variation: Include variation payload on each list row.
        """
        validate_page_size(page_size)
        return self._list_page(
            page_size, page_token, search, type, view, include_variation
        )

    def _list_page(
        self,
        page_size: int,
        page_token: Optional[str],
        search: Optional[str] = None,
        type: Optional[AgentType] = None,
        view: Optional[VariationView] = None,
        include_variation: Optional[bool] = None,
    ) -> Page[Agent]:
        params = _workflows_list_params(
            page_size, page_token, search, type, view, include_variation
        )
        data = with_retry(
            lambda: invoke_operation(
                self._http, self._ops.list, query=params
            ),
            self._config.max_retries,
        )
        return build_aip_page_mapped(
            data,
            "agents",
            _parse_workflow,
            lambda cur: self._list_page(
                page_size, cur, search, type, view, include_variation
            ),
        )

    def get(
        self,
        workflow_id: Union[int, str],
        *,
        view: Optional[VariationView] = None,
    ) -> Agent:
        """
        Retrieve a workflow by ID or slug.

        Args:
            view: Variation view — ``"active"`` (deployed) or ``"draft"``.

        Raises:
            NotFoundError: if no workflow with this ID/slug exists.
        """
        validate_id(workflow_id, name="workflow_id")
        query = {} if view is None else {"view": view}
        data = with_retry(
            lambda: invoke_operation(
                self._http,
                self._ops.get,
                path_params={"id": workflow_id},
                query=query or None,
            ),
            self._config.max_retries,
        )
        return _parse_workflow(data)

    def chat_stream(
        self,
        workflow_id: Union[int, str],
        message: str,
        *,
        model: str,
        thread_id: Optional[str] = None,
        version: Optional[RunVersion] = None,
    ) -> ChatStream:
        """
        Send a message to a workflow and stream the reply token by token.

        Args:
            workflow_id: Workflow ID or slug.
            message:   The message to send.
            model:     Model to run this message with (required). One of the
                       supported model IDs, e.g. ``"claude-sonnet-5"`` or ``"gpt-5.5"``.
            thread_id: Continue an existing conversation; omit to start a new one.
            version:   Run a specific variation — ``"published"`` or ``"draft"``.

        Returns:
            ChatStream you can iterate for text chunks; the final result carries the ``thread_id``.
        """
        return self._ops.stream_session(
            self._agent_http,
            workflow_id,
            message,
            model=model,
            thread_id=thread_id,
            version=version,
        )


class AsyncWorkflowsResource:
    """
    Async read access to Modus workflows.

    await client.workflows.list() → AsyncPage[Agent]
    await client.workflows.get(workflow_id) → Agent

    To create, update, or deploy workflows use modus.management.ModusManagement.
    """

    def __init__(
        self,
        http: AsyncHttpClient,
        agent_http: AsyncHttpClient,
        config: ModusConfig,
        ops: WorkflowsOperations = WORKFLOW_OPERATIONS,
    ) -> None:
        self._http = http
        self._agent_http = agent_http
        self._config = config
        self._ops = ops
        self.runs = AsyncWorkflowRunsResource(http, config, ops.runs)
        self.workflow_actions = AsyncAgentWorkflowActionsResource(http, config)

    async def list(
        self,
        *,
        page_size: int = 25,
        page_token: Optional[str] = None,
        search: Optional[str] = None,
        type: Optional[AgentType] = None,
        view: Optional[VariationView] = None,
        include_variation: Optional[bool] = None,
    ) -> AsyncPage[Agent]:
        """
        List workflows in the organisation.

        Args:
            page_size:         Items per page (default 25).
            page_token:        Opaque token from a previous page's ``next_page_token``.
            search:            Case-insensitive substring filter on the workflow name.
            type:              Filter by workflow type: ``"task"`` or ``"workflow"``.
            view:              Variation view — ``"active"`` (deployed) or ``"draft"``.
            include_variation: Include variation payload on each list row.
        """
        validate_page_size(page_size)
        return await self._list_page(
            page_size, page_token, search, type, view, include_variation
        )

    async def _list_page(
        self,
        page_size: int,
        page_token: Optional[str],
        search: Optional[str] = None,
        type: Optional[AgentType] = None,
        view: Optional[VariationView] = None,
        include_variation: Optional[bool] = None,
    ) -> AsyncPage[Agent]:
        params = _workflows_list_params(
            page_size, page_token, search, type, view, include_variation
        )
        data = await async_with_retry(
            lambda: invoke_operation_async(
                self._http, self._ops.list, query=params
            ),
            self._config.max_retries,
        )
        return build_async_aip_page_mapped(
            data,
            "agents",
            _parse_workflow,
            lambda cur: self._list_page(
                page_size, cur, search, type, view, include_variation
            ),
        )

    async def get(
        self,
        workflow_id: Union[int, str],
        *,
        view: Optional[VariationView] = None,
    ) -> Agent:
        """
        Retrieve a workflow by ID or slug.

        Args:
            view: Variation view — ``"active"`` (deployed) or ``"draft"``.

        Raises:
            NotFoundError: if no workflow with this ID/slug exists.
        """
        validate_id(workflow_id, name="workflow_id")
        query = {} if view is None else {"view": view}
        data = await async_with_retry(
            lambda: invoke_operation_async(
                self._http,
                self._ops.get,
                path_params={"id": workflow_id},
                query=query or None,
            ),
            self._config.max_retries,
        )
        return _parse_workflow(data)

    def chat_stream(
        self,
        workflow_id: Union[int, str],
        message: str,
        *,
        model: str,
        thread_id: Optional[str] = None,
        version: Optional[RunVersion] = None,
    ) -> AsyncChatStream:
        """
        Send a message to a workflow and stream the reply token by token.

        Args:
            workflow_id: Workflow ID or slug.
            message:   The message to send.
            model:     Model to run this message with (required). One of the
                       supported model IDs, e.g. ``"claude-sonnet-5"`` or ``"gpt-5.5"``.
            thread_id: Continue an existing conversation; omit to start a new one.
            version:   Run a specific variation — ``"published"`` or ``"draft"``.

        Returns:
            AsyncChatStream you can iterate for text chunks; the final result carries the ``thread_id``.
        """
        return self._ops.stream_session_async(
            self._agent_http,
            workflow_id,
            message,
            model=model,
            thread_id=thread_id,
            version=version,
        )
