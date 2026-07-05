"""
Registry of Python SDK AIP-158 list operations for contract tests.

Maps operationId → mock URL, response array key, and SDK invocation.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Literal, Optional, Union

from modus import Modus
from modus.management import ModusManagement
from tests.fixtures.api_shapes import (
    SAMPLE_AGENT,
    SAMPLE_CONTEXT_ITEM,
    SAMPLE_RUN,
    SAMPLE_SKILL,
)

ClientKind = Literal["modus", "management"]
Client = Union[Modus, ModusManagement]

OPENAPI_RELATIVE = "distribution/clients/typescript/modus-sdk/src/_generated/public-openapi.json"

REJECTED_LIST_RESPONSE_BODY: Dict[str, Any] = {
    "items": [],
    "nextCursor": None,
}

# OpenAPI GET operations with pageSize not yet exposed on the Python SDK.
SDK_LIST_OPS_EXCLUDED: frozenset[str] = frozenset()

FORBIDDEN_RESPONSE_KEYS = frozenset({"items", "data", "results"})

SAMPLE_VALUE_ENTRY: Dict[str, Any] = {"value": 123}

SAMPLE_MEMORY: Dict[str, Any] = {
    "id": "mem_01",
    "memory": "User prefers bullet points.",
}

SAMPLE_CONNECTION: Dict[str, Any] = {
    "id": "7a3f9d2c-1111-4000-a000-000000000abc",
    "name": "Production Warehouse",
    "type": "postgresql",
}

SAMPLE_SUGGESTION: Dict[str, Any] = {
    "id": "predefined:q1",
    "skill_id": 42,
    "label": "Revenue",
    "prompt": "Show me revenue",
}

SAMPLE_CONVERSATION_LIST_ITEM: Dict[str, Any] = {
    "threadId": "thread-0",
    "skillId": 42,
    "firstMessage": "Hello",
    "title": None,
    "messageCount": 5,
    "createdAt": "2026-01-01T00:00:00.000Z",
    "updatedAt": "2026-01-01T00:00:00.000Z",
    "userIds": ["user-abc"],
}

SAMPLE_ACTIVE_RUN: Dict[str, Any] = {
    "runId": "run-active-1",
    "sessionId": "thread-0",
    "status": "running",
    "message": "Keep working",
    "createdAt": "2026-01-01T00:00:00.000Z",
    "updatedAt": "2026-01-01T00:00:01.000Z",
}


@dataclass(frozen=True)
class ListOperationSpec:
    """One SDK list surface covered by contract tests."""

    operation_id: str
    mock_url_suffix: str
    items_key: str
    wrong_items_key: str
    sample_item: Dict[str, Any]
    client_kind: ClientKind
    invoke: Callable[[Client], Any]
    expected_page_size: int = 25
    mock_base_url: Optional[str] = None
    # Workflow runs use a Pydantic wire model; non-AIP bodies raise ValidationError.
    bad_body_raises_pydantic: bool = False
    extra_success_fields: Optional[Dict[str, Any]] = None


def success_body(spec: ListOperationSpec) -> Dict[str, Any]:
    body: Dict[str, Any] = {
        spec.items_key: [spec.sample_item],
        "nextPageToken": None,
    }
    if spec.extra_success_fields:
        body.update(spec.extra_success_fields)
    return body


def wrong_key_body(spec: ListOperationSpec) -> Dict[str, Any]:
    body: Dict[str, Any] = {
        spec.wrong_items_key: [],
        "nextPageToken": None,
    }
    if spec.extra_success_fields:
        body.update(spec.extra_success_fields)
    return body


def _connections_invoke(client: Client) -> Any:
    return client.connections.list(page_size=25, page_token="tok_abc")


def _suggestions_invoke(client: Client) -> Any:
    return client.suggestions.list(page_size=5, page_token="tok_abc", skill_ids=[7, 42])


def _context_items_invoke(client: Client) -> Any:
    return client.context.items.list(page_size=25, page_token="tok_abc", context_type="note")


def _context_list_values_invoke(client: Client) -> Any:
    return client.context.items.list_values(
        "7a3f9d2c-1111-4000-a000-000000000abc",
        "metric",
        "amount",
        page_size=25,
        page_token="tok_abc",
    )


def _modus_conversations_invoke(client: Client) -> Any:
    return client.modus.conversations.list(
        page_size=25, page_token="tok_abc", kind="modus"
    )


def _scopes_invoke(client: Client) -> Any:
    return client.scopes.list(page_size=25, page_token="tok_abc")


def _workflows_invoke(client: Client) -> Any:
    return client.workflows.list(page_size=25, page_token="tok_abc")


def _workflow_runs_invoke(client: Client) -> Any:
    return client.workflows.runs.list(7, page_size=25, page_token="tok_abc")


def _active_workflow_runs_invoke(client: Client) -> Any:
    return client.workflows.runs.active(page_size=50, page_token="tok_abc")


def _scope_conversations_invoke(client: Client) -> Any:
    return client.scopes.conversations(42).list(page_size=25, page_token="tok_abc")


def _scope_memories_invoke(client: Client) -> Any:
    assert isinstance(client, ModusManagement)
    return client.scopes.memories(42).list(page_size=25, page_token="tok_abc")


SDK_AIP_LIST_OPERATIONS: List[ListOperationSpec] = [
    ListOperationSpec(
        operation_id="ConnectionsController_list",
        mock_url_suffix="/api/v1/connections",
        items_key="connections",
        wrong_items_key="skills",
        sample_item=SAMPLE_CONNECTION,
        client_kind="modus",
        invoke=_connections_invoke,
    ),
    ListOperationSpec(
        operation_id="SuggestionsController_listApproved",
        mock_url_suffix="/api/v1/suggestions/questions",
        items_key="suggestions",
        wrong_items_key="skills",
        sample_item=SAMPLE_SUGGESTION,
        client_kind="modus",
        invoke=_suggestions_invoke,
        expected_page_size=5,
    ),
    ListOperationSpec(
        operation_id="ContextItemsController_list",
        mock_url_suffix="/api/v1/context/items",
        items_key="contextItems",
        wrong_items_key="skills",
        sample_item=SAMPLE_CONTEXT_ITEM,
        client_kind="modus",
        invoke=_context_items_invoke,
    ),
    ListOperationSpec(
        operation_id="ContextItemsController_listValues",
        mock_url_suffix="/api/v1/context/items/7a3f9d2c-1111-4000-a000-000000000abc/values",
        items_key="values",
        wrong_items_key="skills",
        sample_item=SAMPLE_VALUE_ENTRY,
        client_kind="modus",
        invoke=_context_list_values_invoke,
    ),
    ListOperationSpec(
        operation_id="ModusConversationsController_list",
        mock_url_suffix="/api/v1/modus/conversations",
        items_key="conversations",
        wrong_items_key="skills",
        sample_item=SAMPLE_CONVERSATION_LIST_ITEM,
        client_kind="modus",
        invoke=_modus_conversations_invoke,
    ),
    # --- Scopes (/api/v1/scopes; response DTO keeps the ``skills`` envelope key) ---
    ListOperationSpec(
        operation_id="ScopesController_list",
        mock_url_suffix="/api/v1/scopes",
        items_key="skills",
        wrong_items_key="agents",
        sample_item=SAMPLE_SKILL,
        client_kind="modus",
        invoke=_scopes_invoke,
    ),
    ListOperationSpec(
        operation_id="ScopesController_list",
        mock_url_suffix="/api/v1/scopes",
        items_key="skills",
        wrong_items_key="agents",
        sample_item=SAMPLE_SKILL,
        client_kind="management",
        invoke=_scopes_invoke,
    ),
    ListOperationSpec(
        operation_id="ScopeConversationsController_list",
        mock_url_suffix="/api/v1/scopes/42/conversations",
        items_key="conversations",
        wrong_items_key="skills",
        sample_item=SAMPLE_CONVERSATION_LIST_ITEM,
        client_kind="modus",
        invoke=_scope_conversations_invoke,
    ),
    ListOperationSpec(
        operation_id="ScopeMemoriesController_list",
        mock_url_suffix="/api/v1/scopes/42/memories",
        items_key="memories",
        wrong_items_key="skills",
        sample_item=SAMPLE_MEMORY,
        client_kind="management",
        invoke=_scope_memories_invoke,
    ),
    # --- Workflows (/api/v1/workflows; response DTO keeps the ``agents`` envelope key) ---
    ListOperationSpec(
        operation_id="WorkflowsController_list",
        mock_url_suffix="/api/v1/workflows",
        items_key="agents",
        wrong_items_key="skills",
        sample_item=SAMPLE_AGENT,
        client_kind="modus",
        invoke=_workflows_invoke,
    ),
    ListOperationSpec(
        operation_id="WorkflowsController_list",
        mock_url_suffix="/api/v1/workflows",
        items_key="agents",
        wrong_items_key="skills",
        sample_item=SAMPLE_AGENT,
        client_kind="management",
        invoke=_workflows_invoke,
    ),
    ListOperationSpec(
        operation_id="WorkflowRunsController_list",
        mock_url_suffix="/api/v1/workflows/7/runs",
        items_key="runs",
        wrong_items_key="skills",
        sample_item=SAMPLE_RUN,
        client_kind="modus",
        invoke=_workflow_runs_invoke,
        bad_body_raises_pydantic=True,
        extra_success_fields={"counts": {}},
    ),
    ListOperationSpec(
        operation_id="RunLifecycleController_active",
        mock_url_suffix="/agent/v1/runs/active",
        items_key="runs",
        wrong_items_key="skills",
        sample_item=SAMPLE_ACTIVE_RUN,
        client_kind="modus",
        invoke=_active_workflow_runs_invoke,
        expected_page_size=50,
        mock_base_url="https://agent.modus.com",
        bad_body_raises_pydantic=True,
    ),
]

SDK_AIP_LIST_OPERATION_IDS: frozenset[str] = frozenset(
    {spec.operation_id for spec in SDK_AIP_LIST_OPERATIONS}
)
