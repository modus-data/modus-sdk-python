"""Shared API response shapes for respx mocks (camelCase wire JSON)."""

from __future__ import annotations

from typing import Any, Dict

PERMISSION_FIELDS: Dict[str, Any] = {
    "canManage": True,
    "canUse": True,
    "manageDenial": None,
}

DEFAULT_ACCESS_CONFIG: Dict[str, Any] = {
    "visibility": "shared",
    "groupPermissions": {"__everyone__": {"use": True, "manage": True}},
    "guardrails": [],
    "sharedWith": [],
}

SAMPLE_SKILL: Dict[str, Any] = {
    "id": 42,
    "slug": "revenue-analysis",
    "name": "Revenue Analysis",
    "status": "active",
    "description": None,
    "orgUuid": "org-uuid-abc",
    "hasUnpublishedChanges": False,
    "activeVariationId": "var-uuid-001",
    "draftVariationId": None,
    "accessConfig": DEFAULT_ACCESS_CONFIG,
    "createdAt": "2026-01-01T00:00:00.000Z",
    "updatedAt": "2026-01-15T00:00:00.000Z",
    "deletedAt": None,
    **PERMISSION_FIELDS,
}

SAMPLE_AGENT: Dict[str, Any] = {
    "id": 7,
    "slug": "weekly-report",
    "name": "Weekly Revenue Report",
    "status": "active",
    "type": "task",
    "description": None,
    "orgUuid": "org-uuid-abc",
    "hasUnpublishedChanges": False,
    "activeVariationId": "var-uuid-002",
    "draftVariationId": None,
    "isEnabled": True,
    "accessConfig": DEFAULT_ACCESS_CONFIG,
    "createdAt": "2026-01-01T00:00:00.000Z",
    "updatedAt": "2026-01-15T00:00:00.000Z",
    "deletedAt": None,
    **PERMISSION_FIELDS,
}

SAMPLE_CONTEXT_ITEM: Dict[str, Any] = {
    "uid": "7a3f9d2c-1111-4000-a000-000000000abc",
    "orgId": "org-uuid-abc",
    "contextType": "note",
    "description": "Defines the company fiscal year",
    "content": {"text": "Feb 1 – Jan 31"},
    "userFeedback": "positive",
    "topics": ["finance"],
    "connectionId": None,
    "selectionId": None,
    "dataPath": [],
    "createdAt": "2026-01-01T00:00:00.000Z",
    "updatedAt": "2026-01-01T00:00:00.000Z",
}

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

SAMPLE_RUN_DETAIL: Dict[str, Any] = {
    **SAMPLE_RUN,
    "source": "history",
}
