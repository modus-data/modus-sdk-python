"""Shared fixtures for all tests."""

import pytest
from modus import AsyncModus, Modus

TEST_API_KEY = "modus_test_key_abc123"
TEST_BASE_URL = "https://api.modus.com"


@pytest.fixture
def client() -> Modus:
    return Modus(api_key=TEST_API_KEY, base_url=TEST_BASE_URL)


@pytest.fixture
def async_client() -> AsyncModus:
    return AsyncModus(api_key=TEST_API_KEY, base_url=TEST_BASE_URL)


@pytest.fixture
def sample_skill() -> dict:
    return {
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


@pytest.fixture
def sample_agent() -> dict:
    return {
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
