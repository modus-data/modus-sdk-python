"""
Registry of Python SDK AIP-158 list operations for contract tests.

Maps operationId → mock URL, response array key, and SDK invocation.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Literal, Optional, Union

from modus import Modus
from modus.management import ModusManagement

ClientKind = Literal["modus", "management"]
Client = Union[Modus, ModusManagement]

OPENAPI_RELATIVE = (
    "apps/services/modus-api/openapi/v1.json"
)

REJECTED_LIST_RESPONSE_BODY: Dict[str, Any] = {
    "items": [],
    "nextCursor": None,
}

# OpenAPI GET operations with pageSize not yet exposed on the Python SDK.
SDK_LIST_OPS_EXCLUDED: frozenset[str] = frozenset()

FORBIDDEN_RESPONSE_KEYS = frozenset({"items", "data", "results"})

SAMPLE_SKILL: Dict[str, Any] = {
    "id": 42,
    "slug": "revenue-analysis",
    "name": "Revenue Analysis",
    "status": "active",
    "orgUuid": "org-uuid-abc",
    "hasUnpublishedChanges": False,
    "activeVariationId": "var-uuid-001",
    "draftVariationId": None,
    "isEnabled": True,
    "createdAt": "2026-01-01T00:00:00.000Z",
    "updatedAt": "2026-01-15T00:00:00.000Z",
    "deletedAt": None,
}

SAMPLE_AGENT: Dict[str, Any] = {
    "id": 7,
    "slug": "weekly-report",
    "name": "Weekly Revenue Report",
    "status": "active",
    "type": "task",
    "orgUuid": "org-uuid-abc",
    "hasUnpublishedChanges": False,
    "activeVariationId": "var-uuid-002",
    "draftVariationId": None,
    "isEnabled": True,
    "createdAt": "2026-01-01T00:00:00.000Z",
    "updatedAt": "2026-01-15T00:00:00.000Z",
    "deletedAt": None,
}

SAMPLE_CONTEXT_ITEM: Dict[str, Any] = {
    "uid": "7a3f9d2c-1111-4000-a000-000000000abc",
    "contextType": "note",
    "title": "Fiscal Year Definition",
    "description": "Defines the company fiscal year",
    "content": {"text": "Feb 1 – Jan 31"},
    "verificationStatus": "verified",
    "userFeedback": None,
    "topics": ["finance"],
    "connectionId": None,
    "updateSource": "manual",
    "createdAt": "2026-01-01T00:00:00.000Z",
    "updatedAt": "2026-01-01T00:00:00.000Z",
}

SAMPLE_VALUE_ENTRY: Dict[str, Any] = {"value": 123}

SAMPLE_RUN: Dict[str, Any] = {
    "id": "wf_1:temporal-1",
    "workflowId": "wf_1",
    "temporalRunId": "temporal-1",
    "agentId": 7,
    "agentName": "Weekly Revenue Report",
    "agentType": "task",
    "status": "completed",
    "startedAt": "2026-01-01T00:00:00.000Z",
    "endedAt": "2026-01-01T01:00:00.000Z",
}

SAMPLE_MEMORY: Dict[str, Any] = {
    "id": "mem_01",
    "memory": "User prefers bullet points.",
}

SAMPLE_CONNECTION: Dict[str, Any] = {
    "id": "7a3f9d2c-1111-4000-a000-000000000abc",
    "name": "Production Warehouse",
    "type": "postgresql",
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
    # Agent runs use a Pydantic wire model; non-AIP bodies raise ValidationError.
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


def _skills_invoke(client: Client) -> Any:
    return client.skills.list(page_size=25, page_token="tok_abc")


def _agents_invoke(client: Client) -> Any:
    return client.agents.list(page_size=25, page_token="tok_abc")


def _connections_invoke(client: Client) -> Any:
    return client.connections.list(page_size=25, page_token="tok_abc")


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


def _agent_runs_invoke(client: Client) -> Any:
    return client.agents.runs.list(7, page_size=25, page_token="tok_abc")


def _conversations_invoke(client: Client) -> Any:
    return client.skills.conversations(42).list(page_size=25, page_token="tok_abc")


def _conversations_management_invoke(client: Client) -> Any:
    return client.skills.conversations(42).list(page_size=25, page_token="tok_abc")


def _memories_invoke(client: Client) -> Any:
    assert isinstance(client, ModusManagement)
    return client.skills.memories(42).list(page_size=25, page_token="tok_abc")


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
        operation_id="SkillsController_list",
        mock_url_suffix="/api/v1/skills",
        items_key="skills",
        wrong_items_key="agents",
        sample_item=SAMPLE_SKILL,
        client_kind="modus",
        invoke=_skills_invoke,
    ),
    ListOperationSpec(
        operation_id="AgentsController_list",
        mock_url_suffix="/api/v1/agents",
        items_key="agents",
        wrong_items_key="skills",
        sample_item=SAMPLE_AGENT,
        client_kind="modus",
        invoke=_agents_invoke,
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
        operation_id="AutomationRunsController_list",
        mock_url_suffix="/api/v1/agents/7/runs",
        items_key="runs",
        wrong_items_key="skills",
        sample_item=SAMPLE_RUN,
        client_kind="modus",
        invoke=_agent_runs_invoke,
        bad_body_raises_pydantic=True,
        extra_success_fields={"counts": {}},
    ),
    ListOperationSpec(
        operation_id="ConversationsController_list",
        mock_url_suffix="/api/v1/skills/42/conversations",
        items_key="conversations",
        wrong_items_key="skills",
        sample_item=SAMPLE_CONVERSATION_LIST_ITEM,
        client_kind="modus",
        invoke=_conversations_invoke,
    ),
    ListOperationSpec(
        operation_id="SkillsController_list",
        mock_url_suffix="/api/v1/skills",
        items_key="skills",
        wrong_items_key="agents",
        sample_item=SAMPLE_SKILL,
        client_kind="management",
        invoke=_skills_invoke,
    ),
    ListOperationSpec(
        operation_id="AgentsController_list",
        mock_url_suffix="/api/v1/agents",
        items_key="agents",
        wrong_items_key="skills",
        sample_item=SAMPLE_AGENT,
        client_kind="management",
        invoke=_agents_invoke,
    ),
    ListOperationSpec(
        operation_id="ContextItemsController_list",
        mock_url_suffix="/api/v1/context/items",
        items_key="contextItems",
        wrong_items_key="skills",
        sample_item=SAMPLE_CONTEXT_ITEM,
        client_kind="management",
        invoke=_context_items_invoke,
    ),
    ListOperationSpec(
        operation_id="ConversationsController_list",
        mock_url_suffix="/api/v1/skills/42/conversations",
        items_key="conversations",
        wrong_items_key="skills",
        sample_item=SAMPLE_CONVERSATION_LIST_ITEM,
        client_kind="management",
        invoke=_conversations_management_invoke,
    ),
    ListOperationSpec(
        operation_id="MemoriesController_list",
        mock_url_suffix="/api/v1/skills/42/memories",
        items_key="memories",
        wrong_items_key="skills",
        sample_item=SAMPLE_MEMORY,
        client_kind="management",
        invoke=_memories_invoke,
    ),
]

SDK_AIP_LIST_OPERATION_IDS: frozenset[str] = frozenset(
    {spec.operation_id for spec in SDK_AIP_LIST_OPERATIONS}
)
