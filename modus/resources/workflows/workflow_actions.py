"""Execute workflow actions through the agents resource."""
from __future__ import annotations

from typing import Any, AsyncIterator, Dict, Iterator, Mapping, Optional

from ..._config import ModusConfig
from ..._http import AsyncHttpClient, HttpClient
from ..._openapi_invoke import (
    invoke_operation,
    invoke_operation_async,
    invoke_operation_stream,
    invoke_operation_stream_async,
)
from ..._retry import async_with_retry, with_retry
from ..._streaming import parse_sse_stream
from ..._validation import validate_id
from ...types.runs import RunEvent


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


class AgentWorkflowActionsResource:
    def __init__(self, http: HttpClient, config: ModusConfig) -> None:
        self._http = http
        self._config = config

    def execute(self, body: Mapping[str, Any]) -> Iterator[RunEvent]:
        """
        Execute a workflow action and stream its events.

        Args:
            body: Workflow action request fields such as organizationId, sessionId,
                  workflowAction, and runId.
        """
        return _parse_events(
            invoke_operation_stream(
                self._http,
                "WorkflowActionsController_execute",
                json_body=_request_body(body),
            )
        )

    def cancel(self, run_id: str, body: Optional[Mapping[str, Any]] = None) -> None:
        """
        Cancel a workflow action run.

        Args:
            run_id: Run ID to cancel.
            body:   Optional cancellation details.
        """
        validate_id(run_id, name="run_id")
        with_retry(
            lambda: invoke_operation(
                self._http,
                "WorkflowActionsController_cancel",
                path_params={"runId": run_id},
                json_body=_optional_body(body),
            ),
            self._config.max_retries,
        )


class AsyncAgentWorkflowActionsResource:
    def __init__(self, http: AsyncHttpClient, config: ModusConfig) -> None:
        self._http = http
        self._config = config

    async def execute(self, body: Mapping[str, Any]) -> AsyncIterator[RunEvent]:
        """
        Execute a workflow action and stream its events.

        Args:
            body: Workflow action request fields such as organizationId, sessionId,
                  workflowAction, and runId.
        """
        async for event in _parse_events_async(
            invoke_operation_stream_async(
                self._http,
                "WorkflowActionsController_execute",
                json_body=_request_body(body),
            )
        ):
            yield event

    async def cancel(
        self,
        run_id: str,
        body: Optional[Mapping[str, Any]] = None,
    ) -> None:
        """
        Cancel a workflow action run.

        Args:
            run_id: Run ID to cancel.
            body:   Optional cancellation details.
        """
        validate_id(run_id, name="run_id")
        await async_with_retry(
            lambda: invoke_operation_async(
                self._http,
                "WorkflowActionsController_cancel",
                path_params={"runId": run_id},
                json_body=_optional_body(body),
            ),
            self._config.max_retries,
        )
