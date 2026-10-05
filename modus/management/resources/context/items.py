"""Context items resource — full CRUD for modus.management."""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Sequence

from modus._config import ModusConfig
from modus._http import AsyncHttpClient, HttpClient
from modus._openapi_invoke import invoke_operation, invoke_operation_async
from modus._pagination import (
    aip_list_params,
    build_aip_page,
    build_async_aip_page,
)
from modus._query import update_mask_query
from modus._retry import async_with_retry, with_retry
from modus._validation import validate_page_size
from modus.types.pagination import AsyncPage, Page

from ...types.context import (
    ContextItem,
    ContextItemDeletion,
    ContextItemMove,
    ContextItemUpdate,
    UserFeedback,
)


def _context_list_params(
    page_size: int,
    page_token: Optional[str],
    context_type: Optional[str],
    parent_uids: Optional[Sequence[str]] = None,
    ancestor_uids: Optional[Sequence[str]] = None,
    connection_ids: Optional[Sequence[str]] = None,
) -> Dict[str, Any]:
    extra: Dict[str, Any] = {}
    if context_type is not None:
        extra["contextTypes"] = [context_type]
    if parent_uids is not None:
        extra["parentUids"] = list(parent_uids) if len(parent_uids) > 0 else ""
    if ancestor_uids is not None:
        extra["ancestorUids"] = list(ancestor_uids) if len(ancestor_uids) > 0 else ""
    if connection_ids is not None:
        extra["connectionIds"] = list(connection_ids) if len(connection_ids) > 0 else ""
    return aip_list_params(page_size, page_token, **extra)


class ContextItemsResource:
    def __init__(self, http: HttpClient, config: ModusConfig) -> None:
        self._http = http
        self._config = config

    def list(
        self,
        *,
        page_size: int = 25,
        page_token: Optional[str] = None,
        context_type: Optional[str] = None,
        parent_uids: Optional[Sequence[str]] = None,
        ancestor_uids: Optional[Sequence[str]] = None,
        connection_ids: Optional[Sequence[str]] = None,
    ) -> Page[ContextItem]:
        """
        List context items in the knowledge base.

        Args:
            page_size:    Items per page (default 25).
            page_token:   Opaque token from a previous page's ``next_page_token``.
            context_type: Filter by type, e.g. ``"note"``, ``"link"``, ``"saved_query"``.
            parent_uids:  Exact ordered native ancestry chain for direct children.
                          Omit to leave parent unrestricted; pass ``[]`` for the
                          known-empty root. Native UIDs are exact tokens; for a
                          folder's children send ancestry UIDs plus the last
                          ``data_path`` token, not the hashed context-item ``uid``.
            ancestor_uids: Ordered UID ancestry prefix for strict descendants.
                          Omit to leave unrestricted; pass ``[]`` for every item
                          with non-null ancestry.
            connection_ids: Restrict to these connection ids. Omit to leave
                          unfiltered; pass ``[]`` to match none. The Files root
                          is ``connection_ids=["files"]`` with ``parent_uids=[]``.

        Returns:
            Page of context items.

        Example:
            >>> for item in mgmt.context.items.list(
            ...     context_type="note", page_size=25
            ... ).auto_paging_iter():
            ...     print(item.uid, item.description)

            >>> folders = mgmt.context.items.list(
            ...     connection_ids=["files"],
            ...     context_type="file_folder_metadata",
            ...     parent_uids=[],
            ... )
        """
        validate_page_size(page_size)
        return self._list_page(
            page_size,
            page_token,
            context_type,
            parent_uids,
            ancestor_uids,
            connection_ids,
        )

    def _list_page(
        self,
        page_size: int,
        page_token: Optional[str],
        context_type: Optional[str],
        parent_uids: Optional[Sequence[str]] = None,
        ancestor_uids: Optional[Sequence[str]] = None,
        connection_ids: Optional[Sequence[str]] = None,
    ) -> Page[ContextItem]:
        params = _context_list_params(
            page_size,
            page_token,
            context_type,
            parent_uids,
            ancestor_uids,
            connection_ids,
        )
        data = with_retry(
            lambda: invoke_operation(
                self._http, "ContextItemsController_list", query=params
            ),
            self._config.max_retries,
        )
        return build_aip_page(
            data,
            "contextItems",
            ContextItem,
            lambda cur: self._list_page(
                page_size,
                cur,
                context_type,
                parent_uids,
                ancestor_uids,
                connection_ids,
            ),
        )

    def get(self, uid: str) -> ContextItem:
        """
        Retrieve a context item by its UID.

        Args:
            uid: The context item UID.

        Returns:
            The context item.

        Raises:
            NotFoundError: if no item with this UID exists.

        Example:
            >>> item = mgmt.context.items.get("PLACEHOLDER_UID")
            >>> print(item.context_type, item.description)
        """
        data = with_retry(
            lambda: invoke_operation(
                self._http,
                "ContextItemsController_get",
                path_params={"uid": uid},
            ),
            self._config.max_retries,
        )
        return ContextItem.model_validate(data)

    def update(
        self,
        uid: str,
        *,
        content: Optional[Any] = None,
        context_type: Optional[str] = None,
        description: Optional[str] = None,
        user_feedback: UserFeedback | str | None = None,
        topics: Optional[List[str]] = None,
        update_mask: Optional[str] = None,
    ) -> ContextItem:
        """Update a context item.

        Args:
            uid:           UUID of the context item to update.
            content:       Replacement type-specific content, if changing it.
            context_type:  The item's type (e.g. ``"note"``). Required when ``content`` is supplied.
            description:   New description, if changing it.
            user_feedback: Feedback verdict — ``"positive"``, ``"neutral"``, or ``"negative"``.
            topics:        Replacement topic tags. Pass ``[]`` to clear all tags.
            update_mask:   Comma-separated field names to clear. Name a field here and
                           leave its argument unset to set it to null on the server;
                           fields not named in the mask are left untouched.

        Only the fields you pass are changed; omitted fields are left as-is.

        Example:
            >>> updated = mgmt.context.items.update(
            ...     "PLACEHOLDER_UID",
            ...     description="ARR definition (finance)",
            ... )
            >>> print(updated.description)
        """
        feedback: UserFeedback | None = (
            UserFeedback(user_feedback) if user_feedback is not None else None
        )
        payload = ContextItemUpdate(
            content=content,
            context_type=context_type,
            description=description,
            user_feedback=feedback,
            topics=topics,
        ).model_dump(by_alias=True, exclude_none=update_mask is None)
        with_retry(
            lambda: invoke_operation(
                self._http,
                "ContextItemsController_update",
                path_params={"uid": uid},
                query=update_mask_query(update_mask),
                json_body=payload,
            ),
            self._config.max_retries,
        )
        return self.get(uid)

    def delete(self, uid: str) -> ContextItemDeletion:
        """
        Delete a context item from the knowledge base.

        Deleting a Files folder also deletes all contained files and subfolders.

        Args:
            uid: The context item UID.

        Returns:
            Deletion confirmation with the removed item's UID.

        Example:
            >>> mgmt.context.items.delete("PLACEHOLDER_UID")
        """
        raw = with_retry(
            lambda: invoke_operation(
                self._http,
                "ContextItemsController_delete",
                path_params={"uid": uid},
            ),
            self._config.max_retries,
        )
        return ContextItemDeletion.model_validate(raw)

    def move(self, uid: str, *, destination_folder_uid: Optional[str]) -> ContextItemMove:
        """
        Move a live file or Files folder.

        Pass ``destination_folder_uid=None`` to move to the Files root. The
        destination folder must already exist. Same-parent moves succeed as a
        no-op. Does not rename or merge folders.

        Args:
            uid: Stored context-item uid of the file or folder to move.
            destination_folder_uid: Stored context-item uid of the destination
                folder, or ``None`` for the Files root.

        Returns:
            How many items changed parent (``0`` is a successful no-op).

        Raises:
            NotFoundError: The source is missing or not visible.
            ModusError: The destination is missing, not a Files folder, or the
                move would create a cycle (HTTP 400).
            PermissionDeniedError: The destination exists but is not writable
                for this caller.
            ConflictError: A sibling with the same name already exists.

        Example:
            >>> moved = mgmt.context.items.move(
            ...     "PLACEHOLDER_UID",
            ...     destination_folder_uid="PLACEHOLDER_FOLDER_UID",
            ... )
            >>> print(moved.moved_items)
        """
        raw = with_retry(
            lambda: invoke_operation(
                self._http,
                "ContextItemsController_move",
                path_params={"uid": uid},
                json_body={"destinationFolderUid": destination_folder_uid},
            ),
            self._config.max_retries,
        )
        return ContextItemMove.model_validate(raw)


class AsyncContextItemsResource:
    def __init__(self, http: AsyncHttpClient, config: ModusConfig) -> None:
        self._http = http
        self._config = config

    async def list(
        self,
        *,
        page_size: int = 25,
        page_token: Optional[str] = None,
        context_type: Optional[str] = None,
        parent_uids: Optional[Sequence[str]] = None,
        ancestor_uids: Optional[Sequence[str]] = None,
        connection_ids: Optional[Sequence[str]] = None,
    ) -> AsyncPage[ContextItem]:
        """List context items in the knowledge base. See the sync ``list`` for argument details."""
        validate_page_size(page_size)
        return await self._list_page(
            page_size,
            page_token,
            context_type,
            parent_uids,
            ancestor_uids,
            connection_ids,
        )

    async def _list_page(
        self,
        page_size: int,
        page_token: Optional[str],
        context_type: Optional[str],
        parent_uids: Optional[Sequence[str]] = None,
        ancestor_uids: Optional[Sequence[str]] = None,
        connection_ids: Optional[Sequence[str]] = None,
    ) -> AsyncPage[ContextItem]:
        params = _context_list_params(
            page_size,
            page_token,
            context_type,
            parent_uids,
            ancestor_uids,
            connection_ids,
        )
        data = await async_with_retry(
            lambda: invoke_operation_async(
                self._http, "ContextItemsController_list", query=params
            ),
            self._config.max_retries,
        )
        return build_async_aip_page(
            data,
            "contextItems",
            ContextItem,
            lambda cur: self._list_page(
                page_size,
                cur,
                context_type,
                parent_uids,
                ancestor_uids,
                connection_ids,
            ),
        )

    async def get(self, uid: str) -> ContextItem:
        """Retrieve a context item by its UID. See the sync ``get`` for argument details."""
        data = await async_with_retry(
            lambda: invoke_operation_async(
                self._http,
                "ContextItemsController_get",
                path_params={"uid": uid},
            ),
            self._config.max_retries,
        )
        return ContextItem.model_validate(data)

    async def update(
        self,
        uid: str,
        *,
        content: Optional[Any] = None,
        context_type: Optional[str] = None,
        description: Optional[str] = None,
        user_feedback: UserFeedback | str | None = None,
        topics: Optional[List[str]] = None,
        update_mask: Optional[str] = None,
    ) -> ContextItem:
        """Update a context item. See the sync ``update`` for argument details."""
        feedback: UserFeedback | None = (
            UserFeedback(user_feedback) if user_feedback is not None else None
        )
        payload = ContextItemUpdate(
            content=content,
            context_type=context_type,
            description=description,
            user_feedback=feedback,
            topics=topics,
        ).model_dump(by_alias=True, exclude_none=update_mask is None)
        await async_with_retry(
            lambda: invoke_operation_async(
                self._http,
                "ContextItemsController_update",
                path_params={"uid": uid},
                query=update_mask_query(update_mask),
                json_body=payload,
            ),
            self._config.max_retries,
        )
        return await self.get(uid)

    async def delete(self, uid: str) -> ContextItemDeletion:
        """Delete a context item from the knowledge base. See the sync ``delete`` for argument details."""
        raw = await async_with_retry(
            lambda: invoke_operation_async(
                self._http,
                "ContextItemsController_delete",
                path_params={"uid": uid},
            ),
            self._config.max_retries,
        )
        return ContextItemDeletion.model_validate(raw)

    async def move(self, uid: str, *, destination_folder_uid: Optional[str]) -> ContextItemMove:
        """Move a live file or Files folder asynchronously.

        Args:
            uid: Stored context-item uid of the file or folder to move.
            destination_folder_uid: Existing destination folder uid, or ``None``
                for the Files root.

        Returns:
            How many items changed parent; ``0`` is a same-parent no-op.

        Example:
            >>> moved = await mgmt.context.items.move(
            ...     "PLACEHOLDER_UID", destination_folder_uid=None
            ... )
            >>> print(moved.moved_items)
        """
        raw = await async_with_retry(
            lambda: invoke_operation_async(
                self._http,
                "ContextItemsController_move",
                path_params={"uid": uid},
                json_body={"destinationFolderUid": destination_folder_uid},
            ),
            self._config.max_retries,
        )
        return ContextItemMove.model_validate(raw)
