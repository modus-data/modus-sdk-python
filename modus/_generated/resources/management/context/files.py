# Auto-generated from the Modus API schema. Do not edit by hand.

from __future__ import annotations

from typing import Optional

from modus._config import ModusConfig
from modus._http import AsyncHttpClient, HttpClient
from modus._openapi_invoke import invoke_operation, invoke_operation_async
from modus._pagination import aip_list_params, build_aip_page_mapped, build_async_aip_page_mapped
from modus._retry import async_with_retry, with_retry
from modus._validation import validate_id, validate_page_size
from modus.management.types.context_files import FileUpload
from modus.types.pagination import AsyncPage, Page


class _ContextFilesResourceBase:
    """Generated base for the management ``context.files`` resource."""

    def __init__(self, http: HttpClient, config: ModusConfig) -> None:
        self._http = http
        self._config = config

    def list(self, *, page_size: int = 50, page_token: Optional[str] = None) -> Page[FileUpload]:
        """
        List file uploads.

        Returns a page of durable landed file uploads. Uploads that have not landed yet are visible
        via ``GET /context/files/{uploadId}``, not this list.

        **Requires:** ``context:read``

        Args:
            page_size: Items per page. Defaults to 50.
            page_token: Opaque page token from a previous response's ``next_page_token``. Omit for
                the first page.

        Returns:
            A page of files.

        Example:
            >>> for row in mgmt.context.files.list(page_size=25).auto_paging_iter():
            ...     print(row.upload_id, row.file_name, row.status)
        """
        validate_page_size(page_size, max_page_size=200)
        return self._list_page(page_size, page_token)

    def _list_page(self, page_size: int, page_token: Optional[str]) -> Page[FileUpload]:
        params = aip_list_params(page_size, page_token)
        data = with_retry(
            lambda: invoke_operation(
                self._http,
                "ContextFilesController_list",
                query=params,
            ),
            self._config.max_retries,
        )
        return build_aip_page_mapped(
            data,
            "files",
            FileUpload.model_validate,
            lambda cur: self._list_page(page_size, cur),
        )

    def get(self, upload_id: str) -> FileUpload:
        """
        Get a file upload.

        Returns status + metadata for one upload. Prefers the durable landed context item; falls
        back to in-flight upload status while the object has not landed yet. 404 if neither exists.

        **Requires:** ``context:read``

        Args:
            upload_id: Upload id returned by ``create_upload_url`` / ``create_upload_urls``.

        Example:
            >>> upload = mgmt.context.files.get("PLACEHOLDER_UPLOAD_ID")
            >>> print(upload.status, upload.file_name)
        """
        validate_id(upload_id, name="upload_id")
        raw = with_retry(
            lambda: invoke_operation(
                self._http,
                "ContextFilesController_get",
                path_params={"uploadId": upload_id},
            ),
            self._config.max_retries,
        )
        return FileUpload.model_validate(raw)


class _AsyncContextFilesResourceBase:
    """Generated base for the management ``context.files`` resource."""

    def __init__(self, http: AsyncHttpClient, config: ModusConfig) -> None:
        self._http = http
        self._config = config

    async def list(
        self,
        *,
        page_size: int = 50,
        page_token: Optional[str] = None,
    ) -> AsyncPage[FileUpload]:
        """
        List file uploads.

        Returns a page of durable landed file uploads. Uploads that have not landed yet are visible
        via ``GET /context/files/{uploadId}``, not this list.

        **Requires:** ``context:read``

        Args:
            page_size: Items per page. Defaults to 50.
            page_token: Opaque page token from a previous response's ``next_page_token``. Omit for
                the first page.

        Returns:
            A page of files.
        """
        validate_page_size(page_size, max_page_size=200)
        return await self._list_page(page_size, page_token)

    async def _list_page(self, page_size: int, page_token: Optional[str]) -> AsyncPage[FileUpload]:
        params = aip_list_params(page_size, page_token)
        data = await async_with_retry(
            lambda: invoke_operation_async(
                self._http,
                "ContextFilesController_list",
                query=params,
            ),
            self._config.max_retries,
        )
        return build_async_aip_page_mapped(
            data,
            "files",
            FileUpload.model_validate,
            lambda cur: self._list_page(page_size, cur),
        )

    async def get(self, upload_id: str) -> FileUpload:
        """
        Get a file upload.

        Returns status + metadata for one upload. Prefers the durable landed context item; falls
        back to in-flight upload status while the object has not landed yet. 404 if neither exists.

        **Requires:** ``context:read``

        Args:
            upload_id: Upload id returned by ``create_upload_url`` / ``create_upload_urls``.
        """
        validate_id(upload_id, name="upload_id")
        raw = await async_with_retry(
            lambda: invoke_operation_async(
                self._http,
                "ContextFilesController_get",
                path_params={"uploadId": upload_id},
            ),
            self._config.max_retries,
        )
        return FileUpload.model_validate(raw)
