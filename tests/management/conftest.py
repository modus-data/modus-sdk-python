"""Shared fixtures for modus.management tests."""

import pytest

TEST_API_KEY = "modus_test_mgmt_key_abc123"
TEST_BASE_URL = "https://api.modus.com"


@pytest.fixture
def client():
    """A sync ModusManagement client wired to api.modus.com for respx mocking."""
    from modus.management import ModusManagement
    return ModusManagement(api_key=TEST_API_KEY, base_url=TEST_BASE_URL)


@pytest.fixture
async def async_client():
    """An async ModusManagement client wired to api.modus.com for respx mocking."""
    from modus.management import AsyncModusManagement
    async with AsyncModusManagement(api_key=TEST_API_KEY, base_url=TEST_BASE_URL) as c:
        yield c


@pytest.fixture
def skill_list_row() -> dict:
    """A skill as returned by GET /api/v1/skills (list) — no variation."""
    return {
        "id": 10,
        "slug": "snowflake-analyst",
        "name": "Snowflake Analyst",
        "status": "active",
        "description": "Answers data questions using Snowflake",
        "orgUuid": "org-uuid-xyz",
        "hasUnpublishedChanges": False,
        "activeVariationId": "var-001",
        "draftVariationId": None,
        "accessConfig": {"guardrails": ["no-pii"], "permissions": {}},
        "createdAt": "2026-01-01T00:00:00.000Z",
        "updatedAt": "2026-03-01T00:00:00.000Z",
        "deletedAt": None,
    }


@pytest.fixture
def skill_detail_row(skill_list_row) -> dict:
    """A skill as returned by GET /api/v1/skills/:id — includes variation."""
    return {
        **skill_list_row,
        "variation": {
            "instructions": ["You are a Snowflake data analyst.", "Use SQL for queries."],
            "model": "gpt-4o",
            "expectedOutput": "Structured JSON with data rows",
            "toolset": {
                "sql_runner": ["SELECT:conn-snowflake-001:analytics:public"],
                "memory": {"enabled": True},
            },
            "connectionSet": [{"connectionId": "conn-snowflake-001"}],
            "contextSelections": [],
            "interfaces": [],
            "evaluations": [],
        },
    }


@pytest.fixture
def agent_list_row() -> dict:
    """An agent as returned by GET /api/v1/agents (list)."""
    return {
        "id": 5,
        "slug": "weekly-report",
        "name": "Weekly Revenue Report",
        "status": "active",
        "type": "task",
        "description": "Sends weekly revenue summary",
        "orgUuid": "org-uuid-xyz",
        "hasUnpublishedChanges": False,
        "isEnabled": True,
        "activeVariationId": "avar-001",
        "draftVariationId": None,
        "accessConfig": {"guardrails": [], "permissions": {}},
        "createdAt": "2026-01-01T00:00:00.000Z",
        "updatedAt": "2026-02-01T00:00:00.000Z",
        "deletedAt": None,
    }


@pytest.fixture
def agent_detail_row(agent_list_row) -> dict:
    """An agent as returned by GET /api/v1/agents/:id — includes variation."""
    return {
        **agent_list_row,
        "variation": {
            "instructions": ["Run the weekly revenue SQL and email results."],
            "model": "gpt-4o-mini",
        },
    }


@pytest.fixture
def sample_context_item() -> dict:
    return {
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
