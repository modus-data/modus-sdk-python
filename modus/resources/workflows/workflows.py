"""Read-only workflows resource for the consumption client."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Union

from modus._generated.resources.consumption.workflows import (
    _AsyncWorkflowsResourceBase,
    _WorkflowsResourceBase,
)

from ..._chat import AsyncChatSession, ChatSession, start_chat, start_chat_async
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


WORKFLOW_OPERATIONS = WorkflowsOperations(
    list="WorkflowsController_list",
    get="WorkflowsController_get",
    runs=WORKFLOW_RUN_OPERATIONS,
)


def _parse_workflow(raw: dict) -> Agent:
    return WorkflowDto.model_validate(raw)


class WorkflowsResource(_WorkflowsResourceBase):
    """
    Read and run access to Modus workflows.

    - ``list`` / ``get`` — browse workflows (``view="active"``, ``"draft"``, or ``"published"``)
    - ``chat`` — stream a chat turn against one workflow
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
        Retrieve a workflow by its numeric id.

        Args:
            workflow_id: Numeric workflow id.
            view: Variation view — ``"active"`` (deployed), ``"draft"``, or ``"published"``.

        Returns:
            Workflow record (``id``, ``name``, ``status``, …).

        Raises:
            NotFoundError: if no workflow with this id exists.

        Example:
            >>> first = client.workflows.list().items[0]
            >>> wf = client.workflows.get(first.id)
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

    def chat(
        self,
        workflow_id: Union[int, str],
        message: str,
        *,
        model: str,
        thread_id: Optional[str] = None,
    ) -> ChatSession:
        """
        Chat with a published workflow. Node output streams live from the agent
        host: iterate ``text_stream`` for tokens, or call ``result()`` for the
        workflow's final output.

        Prefer ``client.workflows.runs.create`` when you need run lifecycle
        events (cancel / resume).

        Args:
            workflow_id: Numeric workflow id.
            message:   The message to send.
            model:     Model id, e.g. ``"claude-sonnet-5.5"``.
            thread_id: Continue an existing conversation; omit to start a new one.

        Returns:
            ``ChatSession``; ``result()`` gives ``content``, ``thread_id`` and ``run_id``.

        Raises:
            ModusError: No agent host is known for a custom ``base_url``.

        Example:
            >>> result = client.workflows.chat(
            ...     workflow_id,
            ...     "Run the weekly digest summary.",
            ...     model="claude-sonnet-5.5",
            ... ).result()
            >>> print(result.content)
        """
        return start_chat(
            self._agent_http, self._config, "workflows", workflow_id, message, model=model, thread_id=thread_id
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
        Retrieve a workflow by its numeric id.

        Args:
            view: Variation view — ``"active"`` (deployed), ``"draft"``, or ``"published"``.

        Raises:
            NotFoundError: if no workflow with this id exists.
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

    def chat(
        self,
        workflow_id: Union[int, str],
        message: str,
        *,
        model: str,
        thread_id: Optional[str] = None,
    ) -> AsyncChatSession:
        """Chat with a workflow; ``await`` the session for the final output. See the sync ``chat``."""
        return start_chat_async(
            self._agent_http, self._config, "workflows", workflow_id, message, model=model, thread_id=thread_id
        )
