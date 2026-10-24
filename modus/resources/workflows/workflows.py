"""Read-only workflows resource for the consumption client."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Optional, Union

from modus._generated.resources.consumption.workflows import (
    _AsyncWorkflowsResourceBase,
    _WorkflowsResourceBase,
)

from ..._chat import (
    AsyncChatStream,
    ChatStream,
    RunVersion,
    workflow_stream_session,
    workflow_stream_session_async,
)
from ..._config import ModusConfig
from ..._generated.models import WorkflowDto
from ..._http import AsyncHttpClient, HttpClient
from ..._openapi_invoke import invoke_operation, invoke_operation_async
from ..._retry import async_with_retry, with_retry
from ..._validation import validate_id
from ...types.agents import Agent
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
    return WorkflowDto.model_validate(raw)


class WorkflowsResource(_WorkflowsResourceBase):
    """
    Read and run access to Modus workflows.

    - ``list`` / ``get`` — browse workflows (``view="active"`` or ``"draft"``)
    - ``chat_stream`` — stream a chat turn against one workflow
    - ``runs`` — start runs, follow history, cancel / resume

    To create, update, or deploy workflows use ``modus.management.ModusManagement``.

    Example:
        >>> import modus
        >>> client = modus.Modus()
        >>> for wf in client.workflows.list().auto_paging_iter():
        ...     print(wf.id, wf.name, wf.status)
    """

    def __init__(
        self,
        http: HttpClient,
        agent_http: HttpClient,
        config: ModusConfig,
        ops: WorkflowsOperations = WORKFLOW_OPERATIONS,
    ) -> None:
        super().__init__(http, config, ops)
        self._agent_http = agent_http
        self._ops: WorkflowsOperations = ops
        self.runs = WorkflowRunsResource(http, config, ops.runs)
        self.workflow_actions = AgentWorkflowActionsResource(http, config)

    def get(
        self,
        workflow_id: Union[int, str],
        *,
        view: Optional[VariationView] = None,
    ) -> Agent:
        """
        Retrieve a workflow by ID or slug.

        Args:
            workflow_id: Workflow numeric id or slug string.
            view: Variation view — ``"active"`` (deployed) or ``"draft"``.

        Returns:
            Workflow record (``id``, ``name``, ``status``, …).

        Raises:
            NotFoundError: if no workflow with this ID/slug exists.

        Example:
            >>> wf = client.workflows.get("weekly-digest")
            >>> print(wf.name, wf.status)
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
        Stream a workflow reply token by token (SSE).

        Prefer ``client.workflows.runs.create`` when you need run lifecycle
        events (cancel / resume). Use this helper for a chat-shaped stream.

        Args:
            workflow_id: Workflow ID or slug.
            message:   The message to send.
            model:     Model to run this message with (required). One of the
                       supported model IDs, e.g. ``"claude-sonnet-5"`` or ``"gpt-5.5"``.
            thread_id: Continue an existing conversation; omit to start a new one.
            version:   Run a specific variation — ``"published"`` or ``"draft"``.

        Returns:
            ``ChatStream``. After iteration,
            ``stream.get_final_result()`` exposes ``content`` and ``thread_id``.

        Example:
            >>> with client.workflows.chat_stream(
            ...     workflow_id,
            ...     "Run the weekly digest summary.",
            ...     model="claude-sonnet-5",
            ... ) as stream:
            ...     for token in stream.text_stream:
            ...         print(token, end="", flush=True)
        """
        return self._ops.stream_session(
            self._agent_http,
            workflow_id,
            message,
            model=model,
            thread_id=thread_id,
            version=version,
        )


class AsyncWorkflowsResource(_AsyncWorkflowsResourceBase):
    """
    Async read and run access to Modus workflows.

    await client.workflows.list() → AsyncPage[Agent]
    await client.workflows.get(workflow_id) → Agent

    Sync Examples on ``WorkflowsResource`` apply; swap in ``await`` /
    ``async for`` as needed. To create, update, or deploy workflows use
    ``modus.management.ModusManagement``.
    """

    def __init__(
        self,
        http: AsyncHttpClient,
        agent_http: AsyncHttpClient,
        config: ModusConfig,
        ops: WorkflowsOperations = WORKFLOW_OPERATIONS,
    ) -> None:
        super().__init__(http, config, ops)
        self._agent_http = agent_http
        self._ops: WorkflowsOperations = ops
        self.runs = AsyncWorkflowRunsResource(http, config, ops.runs)
        self.workflow_actions = AsyncAgentWorkflowActionsResource(http, config)

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
