"""Context items resource — full CRUD for modus.management."""

from __future__ import annotations

from typing import Any, Dict, List, Mapping, Optional, Sequence, Union

from modus._config import ModusConfig
from modus._exceptions import ValidationError
from modus._http import AsyncHttpClient, HttpClient
from modus._openapi_invoke import invoke_operation, invoke_operation_async
from modus._pagination import (
    aip_list_params,
    build_aip_page,
    build_async_aip_page,
)
from modus._query import update_body, update_mask_query
from modus._retry import async_with_retry, with_retry
from modus._validation import validate_page_size
from modus.types.pagination import AsyncPage, Page

from ...types.context import (
    ContextItem,
    ContextItemAccessUpdate,
    ContextItemDeletion,
    ContextItemGroupPermission,
    ContextItemMove,
    ContextItemSharedUser,
    ContextItemUpdate,
    ContextItemVisibility,
    UserFeedback,
)
from .dashboards import _access_body

VisibilityInput = Union[ContextItemVisibility, str]
GroupPermissionInput = Union[ContextItemGroupPermission, Mapping[str, bool]]
SharedUserInput = Union[ContextItemSharedUser, Mapping[str, Any]]


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


def _move_body(
    destination_folder_uid: Optional[str], destination_folder_path: Optional[str]
) -> Dict[str, Any]:
    if destination_folder_path is None:
        return {"destinationFolderUid": destination_folder_uid}
    if destination_folder_uid is not None:
        raise ValidationError("Pass destination_folder_uid or destination_folder_path, not both")
    return {"destinationFolderPath": destination_folder_path}


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
        payload = update_body(ContextItemUpdate(
            content=content,
            context_type=context_type,
            description=description,
            user_feedback=feedback,
            topics=topics,
        ), update_mask)
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

    def move(
        self,
        uid: str,
        *,
        destination_folder_uid: Optional[str] = None,
        destination_folder_path: Optional[str] = None,
    ) -> ContextItemMove:
        """
        Move a live file or Files folder.

        Pass ``destination_folder_uid`` (an existing folder; ``None`` is the
        Files root) or ``destination_folder_path`` (a root-relative path such as
        ``"reports/2026"``; missing folders on it are created with the move), not
        both. Same-parent moves succeed as a no-op. Does not rename or merge folders.

        Args:
            uid: Stored context-item uid of the file or folder to move.
            destination_folder_uid: Stored context-item uid of the destination
                folder, or ``None`` for the Files root.
            destination_folder_path: Root-relative destination folder path.

        Returns:
            How many items changed parent (``0`` is a successful no-op).

        Raises:
            NotFoundError: The source is missing or not visible.
            ModusError: The destination is missing, not a Files folder, or the
                move would create a cycle (HTTP 400).
            PermissionDeniedError: The destination exists but is not writable
                for this caller.
            ConflictError: A sibling with the same name already exists.
            ValidationError: Both destinations were given.

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
                json_body=_move_body(destination_folder_uid, destination_folder_path),
            ),
            self._config.max_retries,
        )
        return ContextItemMove.model_validate(raw)

    def update_access(
        self,
        uid: str,
        *,
        visibility: VisibilityInput,
        group_permissions: Mapping[str, GroupPermissionInput],
        shared_with: Sequence[SharedUserInput],
    ) -> ContextItemAccessUpdate:
        """Replace who can view and manage a note, saved query, link or uploaded file.

        All three settings are required and replace the current ones. You cannot
        remove your own manage access. An item created before items had owners
        becomes yours on the first change.

        Args:
            uid: UUID of the context item.
            visibility: ``shared`` (the owner plus the groups in ``group_permissions``)
                or ``private`` (the owner plus the users in ``shared_with``).
            group_permissions: Group id to ``ContextItemGroupPermission`` or a dict
                such as ``{"use": True, "manage": False}``. Used only when shared.
            shared_with: Users as ``ContextItemSharedUser`` values or dicts such as
                ``{"email": "ana@example.com", "permission": "use"}``. Used only
                when private.

        Returns:
            The item's new access settings and whether you can still manage it.

        Raises:
            NotFoundError: The item does not exist or you cannot view it.
            PermissionDeniedError: You can view the item but not manage it.
            ModusError: The item is another type, a group or user is invalid, or
                the change would remove your own manage access.

        Example:
            >>> mgmt.context.items.update_access(
            ...     "PLACEHOLDER_UID",
            ...     visibility="private",
            ...     group_permissions={},
            ...     shared_with=[{"email": "ana@example.com", "permission": "use"}],
            ... )
        """
        body = _access_body(visibility, group_permissions, shared_with)
        raw = with_retry(
            lambda: invoke_operation(
                self._http,
                "ContextItemAccessController_updateAccess",
                path_params={"uid": uid},
                json_body=body,
            ),
            self._config.max_retries,
        )
        return ContextItemAccessUpdate.model_validate(raw)


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
        payload = update_body(ContextItemUpdate(
            content=content,
            context_type=context_type,
            description=description,
            user_feedback=feedback,
            topics=topics,
        ), update_mask)
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

    async def move(
        self,
        uid: str,
        *,
        destination_folder_uid: Optional[str] = None,
        destination_folder_path: Optional[str] = None,
    ) -> ContextItemMove:
        """Move a live file or Files folder asynchronously.

        Args:
            uid: Stored context-item uid of the file or folder to move.
            destination_folder_uid: Existing destination folder uid, or ``None``
                for the Files root.
            destination_folder_path: Root-relative destination folder path; missing
                folders on it are created with the move. Not with
                ``destination_folder_uid``.

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
                json_body=_move_body(destination_folder_uid, destination_folder_path),
            ),
            self._config.max_retries,
        )
        return ContextItemMove.model_validate(raw)

    async def update_access(
        self,
        uid: str,
        *,
        visibility: VisibilityInput,
        group_permissions: Mapping[str, GroupPermissionInput],
        shared_with: Sequence[SharedUserInput],
    ) -> ContextItemAccessUpdate:
        """Replace who can view and manage an item asynchronously. See the sync ``update_access``.

        Example:
            >>> await mgmt.context.items.update_access(
            ...     "PLACEHOLDER_UID",
            ...     visibility="shared",
            ...     group_permissions={"GROUP_ID": {"use": True, "manage": False}},
            ...     shared_with=[],
            ... )
        """
        body = _access_body(visibility, group_permissions, shared_with)
        raw = await async_with_retry(
            lambda: invoke_operation_async(
                self._http,
                "ContextItemAccessController_updateAccess",
                path_params={"uid": uid},
                json_body=body,
            ),
            self._config.max_retries,
        )
        return ContextItemAccessUpdate.model_validate(raw)
