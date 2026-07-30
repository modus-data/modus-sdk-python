"""Context resource — knowledge base management (modus.management)."""

from __future__ import annotations

from typing import List, Optional

from modus._config import ModusConfig
from modus._generated.models import (
    CreateLinkDto,
    CreateNoteDto,
    CreateSavedQueryDto,
)
from modus._http import AsyncHttpClient, HttpClient
from modus._openapi_invoke import invoke_operation, invoke_operation_async
from modus._retry import async_with_retry, with_retry

from ...types.context import ContextItem, CreatedContextItem, UserFeedback
from ._content_merge import (
    async_resolve_existing_content,
    async_update_with_merged_content,
    merge_link_content,
    merge_note_content,
    merge_saved_query_content,
    resolve_existing_content,
    update_with_merged_content,
)
from .custom_items import AsyncCustomContextItemsResource, CustomContextItemsResource
from .items import AsyncContextItemsResource, ContextItemsResource


class ContextResource:
    """
    Full knowledge base access for modus.management.ModusManagement.

    mgmt.context.items.list()               → Page[ContextItem]
    mgmt.context.items.get(uid)             → ContextItem
    mgmt.context.items.update(uid, ...)     → ContextItem
    mgmt.context.items.delete(uid)          → ContextItemDeletion
    mgmt.context.create_note(title, content)              → CreatedContextItem
    mgmt.context.update_note(uid, title=..., body=...)    → ContextItem
    mgmt.context.create_saved_query(name, query, ...)     → CreatedContextItem
    mgmt.context.update_saved_query(uid, name=..., ...)   → ContextItem
    mgmt.context.create_link(url, ...)                    → CreatedContextItem
    mgmt.context.update_link(uid, title=..., url=...)     → ContextItem
    """

    def __init__(self, http: HttpClient, config: ModusConfig) -> None:
        self._http = http
        self._config = config
        self.items = ContextItemsResource(http, config)
        self.custom_items = CustomContextItemsResource(http, config)

    def _create(self, operation_id: str, payload: dict) -> CreatedContextItem:
        data = with_retry(
            lambda: invoke_operation(
                self._http, operation_id, json_body=payload
            ),
            self._config.max_retries,
        )
        return CreatedContextItem.model_validate(data)

    def create_note(self, title: str, content: str) -> CreatedContextItem:
        """Add a free-form text note to the Modus knowledge base.

        Args:
            title:   Display title for the note.
            content: Markdown body text.

        Returns:
            Created item with its new ``uid``.
        """
        body = CreateNoteDto(title=title, content=content)
        return self._create(
            "ContextCreatorsController_createNote",
            body.model_dump(by_alias=True, exclude_none=True),
        )

    def update_note(
        self,
        uid: str,
        *,
        title: str,
        body: str,
        existing: ContextItem | None = None,
        description: Optional[str] = None,
        user_feedback: UserFeedback | str | None = None,
        topics: Optional[List[str]] = None,
    ) -> ContextItem:
        """Update a note's title and markdown body.

        Preserves server-owned fields (``noteId``, ``s3Key``, …) on the
        existing ``content`` blob. Pass ``existing`` to skip a GET when you
        already have the item from a list call.
        """
        content = resolve_existing_content(
            self.items, uid, context_type="note", existing=existing
        )
        merged = merge_note_content(content, title=title, body=body)
        return update_with_merged_content(
            self.items,
            uid,
            context_type="note",
            merged_content=merged,
            existing=existing,
            description=description,
            user_feedback=user_feedback,
            topics=topics,
        )

    def create_saved_query(
        self, name: str, query: Optional[str] = None, *, connection_id: str,
        description: Optional[str] = None, path: Optional[List[str]] = None,
    ) -> CreatedContextItem:
        """Save a SQL query to the Modus knowledge base.

        Args:
            name:          Display name for the saved query.
            query:         SQL text (optional at create if you set it later).
            connection_id: Data connection the query runs against.
            description:   Optional human-readable description.
            path:          Optional hierarchical path segments for organisation.

        Returns:
            Created item with its new ``uid``.
        """
        body = CreateSavedQueryDto(
            name=name,
            query=query,
            connection_id=connection_id,
            description=description,
            path=path,
        )
        return self._create(
            "ContextCreatorsController_createSavedQuery",
            body.model_dump(by_alias=True, exclude_none=True),
        )

    def update_saved_query(
        self,
        uid: str,
        *,
        name: str,
        query: str,
        connection_id: Optional[str] = None,
        path: Optional[List[str]] = None,
        existing: ContextItem | None = None,
        description: Optional[str] = None,
        user_feedback: UserFeedback | str | None = None,
        topics: Optional[List[str]] = None,
    ) -> ContextItem:
        """Update a saved query's name, SQL, and optional connection metadata."""
        content = resolve_existing_content(
            self.items, uid, context_type="saved_query", existing=existing
        )
        merged = merge_saved_query_content(
            content,
            name=name,
            query=query,
            connection_id=connection_id,
            path=path,
        )
        return update_with_merged_content(
            self.items,
            uid,
            context_type="saved_query",
            merged_content=merged,
            existing=existing,
            description=description,
            user_feedback=user_feedback,
            topics=topics,
        )

    def create_link(
        self, url: str, *, title: Optional[str] = None,
        is_crawl: Optional[bool] = None, page_limit: Optional[int] = None,
    ) -> CreatedContextItem:
        """Add a URL to the Modus knowledge base.

        Args:
            url:        Link target URL.
            title:      Optional display title.
            is_crawl:   When ``True``, fetch and index page content.
            page_limit: Maximum pages to crawl when ``is_crawl`` is ``True``.

        Returns:
            Created item with its new ``uid``.
        """
        body = CreateLinkDto(
            url=url,
            title=title,
            is_crawl=is_crawl,
            page_limit=page_limit,
        )
        return self._create(
            "ContextCreatorsController_createLink",
            body.model_dump(by_alias=True, exclude_none=True),
        )

    def update_link(
        self,
        uid: str,
        *,
        title: Optional[str] = None,
        url: Optional[str] = None,
        existing: ContextItem | None = None,
        description: Optional[str] = None,
        user_feedback: UserFeedback | str | None = None,
        topics: Optional[List[str]] = None,
    ) -> ContextItem:
        """Update link metadata on an existing item.

        Merges ``title`` and/or ``url`` into the stored ``content`` blob.
        Does not re-fetch or re-crawl the URL.
        """
        if title is None and url is None and description is None and user_feedback is None and topics is None:
            raise ValueError("Provide at least one field to update.")
        if title is None and url is None:
            return self.items.update(
                uid,
                description=description,
                user_feedback=user_feedback,
                topics=topics,
            )
        content = resolve_existing_content(
            self.items, uid, context_type="link", existing=existing
        )
        merged = merge_link_content(content, title=title, url=url)
        return update_with_merged_content(
            self.items,
            uid,
            context_type="link",
            merged_content=merged,
            existing=existing,
            description=description,
            user_feedback=user_feedback,
            topics=topics,
        )


class AsyncContextResource:
    def __init__(self, http: AsyncHttpClient, config: ModusConfig) -> None:
        self._http = http
        self._config = config
        self.items = AsyncContextItemsResource(http, config)
        self.custom_items = AsyncCustomContextItemsResource(http, config)

    async def _create(self, operation_id: str, payload: dict) -> CreatedContextItem:
        data = await async_with_retry(
            lambda: invoke_operation_async(
                self._http, operation_id, json_body=payload
            ),
            self._config.max_retries,
        )
        return CreatedContextItem.model_validate(data)

    async def create_note(self, title: str, content: str) -> CreatedContextItem:
        """Add a free-form text note to the Modus knowledge base."""
        body = CreateNoteDto(title=title, content=content)
        return await self._create(
            "ContextCreatorsController_createNote",
            body.model_dump(by_alias=True, exclude_none=True),
        )

    async def update_note(
        self,
        uid: str,
        *,
        title: str,
        body: str,
        existing: ContextItem | None = None,
        description: Optional[str] = None,
        user_feedback: UserFeedback | str | None = None,
        topics: Optional[List[str]] = None,
    ) -> ContextItem:
        """Update a note's title and markdown body."""
        content = await async_resolve_existing_content(
            self.items, uid, context_type="note", existing=existing
        )
        merged = merge_note_content(content, title=title, body=body)
        return await async_update_with_merged_content(
            self.items,
            uid,
            context_type="note",
            merged_content=merged,
            existing=existing,
            description=description,
            user_feedback=user_feedback,
            topics=topics,
        )

    async def create_saved_query(
        self, name: str, query: Optional[str] = None, *, connection_id: str,
        description: Optional[str] = None, path: Optional[List[str]] = None,
    ) -> CreatedContextItem:
        """Save a SQL query to the Modus knowledge base. See the sync ``create_saved_query`` for argument details."""
        body = CreateSavedQueryDto(
            name=name,
            query=query,
            connection_id=connection_id,
            description=description,
            path=path,
        )
        return await self._create(
            "ContextCreatorsController_createSavedQuery",
            body.model_dump(by_alias=True, exclude_none=True),
        )

    async def update_saved_query(
        self,
        uid: str,
        *,
        name: str,
        query: str,
        connection_id: Optional[str] = None,
        path: Optional[List[str]] = None,
        existing: ContextItem | None = None,
        description: Optional[str] = None,
        user_feedback: UserFeedback | str | None = None,
        topics: Optional[List[str]] = None,
    ) -> ContextItem:
        """Update a saved query's name, SQL, and optional connection metadata."""
        content = await async_resolve_existing_content(
            self.items, uid, context_type="saved_query", existing=existing
        )
        merged = merge_saved_query_content(
            content,
            name=name,
            query=query,
            connection_id=connection_id,
            path=path,
        )
        return await async_update_with_merged_content(
            self.items,
            uid,
            context_type="saved_query",
            merged_content=merged,
            existing=existing,
            description=description,
            user_feedback=user_feedback,
            topics=topics,
        )

    async def create_link(
        self, url: str, *, title: Optional[str] = None,
        is_crawl: Optional[bool] = None, page_limit: Optional[int] = None,
    ) -> CreatedContextItem:
        """Add a URL to the Modus knowledge base. See the sync ``create_link`` for argument details."""
        body = CreateLinkDto(
            url=url,
            title=title,
            is_crawl=is_crawl,
            page_limit=page_limit,
        )
        return await self._create(
            "ContextCreatorsController_createLink",
            body.model_dump(by_alias=True, exclude_none=True),
        )

    async def update_link(
        self,
        uid: str,
        *,
        title: Optional[str] = None,
        url: Optional[str] = None,
        existing: ContextItem | None = None,
        description: Optional[str] = None,
        user_feedback: UserFeedback | str | None = None,
        topics: Optional[List[str]] = None,
    ) -> ContextItem:
        """Update link metadata on an existing item."""
        if title is None and url is None and description is None and user_feedback is None and topics is None:
            raise ValueError("Provide at least one field to update.")
        if title is None and url is None:
            return await self.items.update(
                uid,
                description=description,
                user_feedback=user_feedback,
                topics=topics,
            )
        content = await async_resolve_existing_content(
            self.items, uid, context_type="link", existing=existing
        )
        merged = merge_link_content(content, title=title, url=url)
        return await async_update_with_merged_content(
            self.items,
            uid,
            context_type="link",
            merged_content=merged,
            existing=existing,
            description=description,
            user_feedback=user_feedback,
            topics=topics,
        )
