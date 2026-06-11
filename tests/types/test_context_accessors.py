"""Unit tests for context read accessors."""

from __future__ import annotations

from modus._generated.models import ContextItemDto, UserFeedback
from modus.types.context_accessors import (
    context_item_label,
    is_verified,
    link_title,
    link_url,
    note_body,
    note_title,
    saved_query_name,
    saved_query_sql,
)
from tests.fixtures.context_content import LINK_CONTENT, NOTE_CONTENT, SAVED_QUERY_CONTENT


def _item(context_type: str, content: dict, **kwargs) -> ContextItemDto:
    return ContextItemDto.model_validate(
        {
            "uid": "uid-001",
            "orgId": "org-001",
            "contextType": context_type,
            "content": content,
            "description": kwargs.get("description"),
            "userFeedback": kwargs.get("user_feedback", "neutral"),
            "topics": kwargs.get("topics", []),
            "connectionId": None,
            "selectionId": None,
            "dataPath": [],
            "createdAt": "2026-01-01T00:00:00.000Z",
            "updatedAt": "2026-01-01T00:00:00.000Z",
        }
    )


def test_note_accessors() -> None:
    item = _item("note", NOTE_CONTENT)
    assert note_title(item) == "Fiscal Year"
    assert note_body(item) == "Feb 1 – Jan 31."


def test_link_accessors() -> None:
    item = _item("link", LINK_CONTENT)
    assert link_title(item) == "Python json docs"
    assert link_url(item) == "https://docs.python.org/3/library/json.html"


def test_saved_query_accessors() -> None:
    item = _item("saved_query", SAVED_QUERY_CONTENT)
    assert saved_query_name(item) == "Top Customers"
    assert saved_query_sql(item) == "SELECT id FROM customers LIMIT 10"


def test_context_item_label_prefers_title_then_description() -> None:
    item = _item("note", NOTE_CONTENT, description="ignored when title present")
    assert context_item_label(item) == "Fiscal Year"
    item2 = _item("note", {}, description="Fallback description")
    assert context_item_label(item2) == "Fallback description"


def test_is_verified() -> None:
    positive = _item("note", NOTE_CONTENT, user_feedback=UserFeedback.positive)
    neutral = _item("note", NOTE_CONTENT, user_feedback=UserFeedback.neutral)
    assert is_verified(positive) is True
    assert is_verified(neutral) is False
