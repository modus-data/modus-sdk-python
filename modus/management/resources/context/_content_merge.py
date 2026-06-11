"""Merge helpers for user-created context item content blobs."""

from __future__ import annotations

from typing import Any

from modus.types.context import ContextItem

from ...types.context import UserFeedback
from .items import AsyncContextItemsResource, ContextItemsResource


def merge_note_content(existing: dict[str, Any], *, title: str, body: str) -> dict[str, Any]:
    """Build note ``content`` for ``items.update``, preserving server-owned keys."""
    return {**existing, "title": title, "content": body}


def merge_link_content(
    existing: dict[str, Any],
    *,
    title: str | None = None,
    url: str | None = None,
) -> dict[str, Any]:
    """Build link ``content`` for ``items.update``. Does not re-fetch the URL."""
    merged = dict(existing)
    if title is not None:
        merged["title"] = title
    if url is not None:
        merged["url"] = url
    return merged


def merge_saved_query_content(
    existing: dict[str, Any],
    *,
    name: str,
    query: str,
    connection_id: str | None = None,
    path: list[str] | None = None,
) -> dict[str, Any]:
    """Build saved_query ``content`` for ``items.update``."""
    merged: dict[str, Any] = {**existing, "name": name, "query": query}
    if connection_id is not None:
        merged["connectionId"] = connection_id
    if path is not None:
        merged["path"] = path
    return merged


def _require_content_dict(item: ContextItem, *, context_type: str) -> dict[str, Any]:
    if item.context_type != context_type:
        raise ValueError(
            f"Expected context_type {context_type!r}, got {item.context_type!r}."
        )
    content = item.content
    if not isinstance(content, dict):
        raise ValueError(
            f"Context item {item.uid!r} has no dict content; cannot merge {context_type} fields."
        )
    return content


def update_with_merged_content(
    items: ContextItemsResource,
    uid: str,
    *,
    context_type: str,
    merged_content: dict[str, Any],
    existing: ContextItem | None = None,
    description: str | None = None,
    user_feedback: UserFeedback | str | None = None,
    topics: list[str] | None = None,
) -> ContextItem:
    if existing is not None:
        _require_content_dict(existing, context_type=context_type)
    return items.update(
        uid,
        context_type=context_type,
        content=merged_content,
        description=description,
        user_feedback=user_feedback,
        topics=topics,
    )


async def async_update_with_merged_content(
    items: AsyncContextItemsResource,
    uid: str,
    *,
    context_type: str,
    merged_content: dict[str, Any],
    existing: ContextItem | None = None,
    description: str | None = None,
    user_feedback: UserFeedback | str | None = None,
    topics: list[str] | None = None,
) -> ContextItem:
    if existing is not None:
        _require_content_dict(existing, context_type=context_type)
    return await items.update(
        uid,
        context_type=context_type,
        content=merged_content,
        description=description,
        user_feedback=user_feedback,
        topics=topics,
    )


def resolve_existing_content(
    items: ContextItemsResource,
    uid: str,
    *,
    context_type: str,
    existing: ContextItem | None,
) -> dict[str, Any]:
    item = existing if existing is not None else items.get(uid)
    return _require_content_dict(item, context_type=context_type)


async def async_resolve_existing_content(
    items: AsyncContextItemsResource,
    uid: str,
    *,
    context_type: str,
    existing: ContextItem | None,
) -> dict[str, Any]:
    item = existing if existing is not None else await items.get(uid)
    return _require_content_dict(item, context_type=context_type)
