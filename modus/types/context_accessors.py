"""Read accessors for well-known context item content shapes (Tier B ergonomics)."""

from __future__ import annotations

from typing import Any

from .context import ContextItem


def _content_dict(item: ContextItem) -> dict[str, Any] | None:
    content = item.content
    return content if isinstance(content, dict) else None


def _enum_value(value: Any) -> str:
    return value.value if hasattr(value, "value") else str(value)


def note_title(item: ContextItem) -> str | None:
    """Display title from a note item's ``content`` blob."""
    content = _content_dict(item)
    if content is None:
        return None
    title = content.get("title")
    return title if isinstance(title, str) and title else None


def note_body(item: ContextItem) -> str | None:
    """Markdown body from a note item's ``content`` blob."""
    content = _content_dict(item)
    if content is None:
        return None
    body = content.get("content")
    return body if isinstance(body, str) else None


def link_title(item: ContextItem) -> str | None:
    """Display title from a link item's ``content`` blob."""
    content = _content_dict(item)
    if content is None:
        return None
    title = content.get("title")
    return title if isinstance(title, str) and title else None


def link_url(item: ContextItem) -> str | None:
    """Source URL from a link item's ``content`` blob."""
    content = _content_dict(item)
    if content is None:
        return None
    url = content.get("url")
    return url if isinstance(url, str) and url else None


def saved_query_name(item: ContextItem) -> str | None:
    """Name from a saved_query item's ``content`` blob."""
    content = _content_dict(item)
    if content is None:
        return None
    name = content.get("name")
    return name if isinstance(name, str) and name else None


def saved_query_sql(item: ContextItem) -> str | None:
    """SQL text from a saved_query item's ``content`` blob."""
    content = _content_dict(item)
    if content is None:
        return None
    query = content.get("query")
    return query if isinstance(query, str) else None


def context_item_label(item: ContextItem, *, fallback: str = "(no title)") -> str:
    """Best-effort human label for any context item."""
    content = _content_dict(item)
    if content is not None:
        for key in ("title", "name"):
            value = content.get(key)
            if isinstance(value, str) and value:
                return value
    description = item.description
    if isinstance(description, str) and description:
        return description
    return fallback or item.uid[:8]


def is_verified(item: ContextItem) -> bool:
    """Whether the item has positive user feedback."""
    return _enum_value(item.user_feedback) == "positive"
