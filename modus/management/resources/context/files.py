"""Context files resource — durable file uploads for modus.management."""

from __future__ import annotations

import asyncio
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Iterator, List, Literal, Optional, Sequence, Tuple, Union

import httpx

from modus._config import ModusConfig
from modus._exceptions import ModusError
from modus._http import AsyncHttpClient, HttpClient
from modus._openapi_invoke import invoke_operation, invoke_operation_async
from modus._pagination import (
    aip_list_params,
    build_aip_page,
    build_async_aip_page,
)
from modus._retry import async_with_retry, with_retry
from modus._validation import validate_id, validate_page_size
from modus.types.pagination import AsyncPage, Page

from ...types.context_files import (
    BulkUploadFromUrlsResult,
    BulkUploadUrlsResult,
    FileUpload,
    UploadDirFailure,
    UploadDirResult,
    UploadFromUrlInput,
    UploadUrlInput,
    UploadUrlSlot,
)

# Bulk `create_upload_urls` / `upload_from_urls` request cap — matches the backend.
MAX_BULK_UPLOAD_FILES = 100

_DEFAULT_LIST_PAGE_SIZE = 50
_DEFAULT_PUT_TIMEOUT_S = 60.0
_STATUS_ORDER = {"pending": 0, "processing": 1, "ready": 2}
_WAIT_UNTIL_VALUES = ("processing", "ready")

# The server owns the extension->MIME table (`EXTENSION_MIME_MAP` in
# `@modus/file-uploads`) and resolves it whenever a client sends
# `application/octet-stream`. Sending that instead of guessing locally keeps one
# source of truth: `mimetypes` results vary by platform and Python version, so a
# local guess can differ from the TypeScript SDK's for the same file and then be
# rejected by the server's allow-list.
DEFER_CONTENT_TYPE_TO_SERVER = "application/octet-stream"

WaitUntil = Literal["processing", "ready"]

_SlotAssignment = Tuple[Path, UploadUrlSlot]


def _validate_wait_until(wait_until: str) -> None:
    if wait_until not in _WAIT_UNTIL_VALUES:
        raise ValueError(f"wait_until must be one of {_WAIT_UNTIL_VALUES!r}, got {wait_until!r}")


def _validate_bulk_size(count: int, *, name: str) -> None:
    if count == 0:
        raise ValueError(f"{name} must not be empty")
    if count > MAX_BULK_UPLOAD_FILES:
        raise ValueError(f"{name} must have at most {MAX_BULK_UPLOAD_FILES} entries, got {count}")


def _slot_content_type(slot: UploadUrlSlot, file_name: str) -> str:
    # `content_type` is required on the wire; the generated type is `str | None`
    # only due to codegen field-name reuse across DTOs. Fall back to the
    # defer-to-server sentinel rather than guessing.
    return slot.content_type or DEFER_CONTENT_TYPE_TO_SERVER


def _status_value(item: FileUpload) -> str:
    status = item.status
    return status.value if hasattr(status, "value") else str(status)


def _status_satisfies(status: str, wait_until: str) -> bool:
    if status == "failed":
        return True
    return _STATUS_ORDER.get(status, 0) >= _STATUS_ORDER[wait_until]


def _chunked(items: Sequence[Path], size: int) -> Iterator[Sequence[Path]]:
    for i in range(0, len(items), size):
        yield items[i : i + size]


def _walk_files(root: Path, *, recursive: bool) -> List[Path]:
    """Regular files under root, skipping hidden files/dirs and symlinks."""
    entries = root.rglob("*") if recursive else root.iterdir()
    files: List[Path] = []
    for entry in sorted(entries):
        if entry.is_symlink():
            continue
        if any(part.startswith(".") for part in entry.relative_to(root).parts):
            continue
        if entry.is_file():
            files.append(entry)
    return files


def _raise_for_put_error(response: httpx.Response) -> None:
    if response.is_error:
        raise ModusError(
            f"Upload PUT to presigned URL failed with HTTP {response.status_code}.",
            status_code=response.status_code,
            body=response.text[:500] if response.text else None,
        )


def _put_bytes_sync(url: str, data: bytes, content_type: str, timeout: float) -> None:
    response = httpx.put(url, content=data, headers={"Content-Type": content_type}, timeout=timeout)
    _raise_for_put_error(response)


async def _put_bytes_async(url: str, data: bytes, content_type: str, timeout: float) -> None:
    async with httpx.AsyncClient(timeout=timeout) as client:
        response = await client.put(url, content=data, headers={"Content-Type": content_type})
    _raise_for_put_error(response)


def _create_slots_payload(files: Sequence[UploadUrlInput]) -> dict:
    return {
        "files": [
            {"fileName": f.file_name, "contentType": f.content_type, "fileSize": f.file_size}
            for f in files
        ]
    }


def _upload_from_urls_payload(urls: Sequence[UploadFromUrlInput]) -> dict:
    return {
        "urls": [
            {"url": u.url, **({"fileName": u.file_name} if u.file_name else {})} for u in urls
        ]
    }


# simplification: batch entries use the file's basename as `fileName`, not the
# path relative to the upload_dir root — nested directories with same-named
# files are indistinguishable once landed. Upgrade path: send the relative
# path as `fileName` once callers need to reconstruct directory structure.
def _slot_inputs_for_batch(
    batch: Sequence[Path], failed: List[UploadDirFailure]
) -> tuple[List[Path], List[UploadUrlInput]]:
    readable: List[Path] = []
    inputs: List[UploadUrlInput] = []
    for p in batch:
        try:
            inputs.append(
                UploadUrlInput(
                    file_name=p.name,
                    content_type=DEFER_CONTENT_TYPE_TO_SERVER,
                    file_size=p.stat().st_size,
                )
            )
            readable.append(p)
        except OSError as exc:
            failed.append(UploadDirFailure(path=str(p), error=str(exc)))
    return readable, inputs


def _assign_slots(
    batch: Sequence[Path], result: BulkUploadUrlsResult, failed: List[UploadDirFailure]
) -> List[_SlotAssignment]:
    failed_indices = {int(f.index) for f in result.failed}
    for f in result.failed:
        failed.append(UploadDirFailure(path=str(batch[int(f.index)]), error=f.error))
    remaining = [p for i, p in enumerate(batch) if i not in failed_indices]
    uploaded = list(result.uploaded)
    if len(uploaded) < len(remaining):
        for p in remaining[len(uploaded) :]:
            failed.append(
                UploadDirFailure(
                    path=str(p),
                    error="Server returned fewer upload slots than requested files.",
                )
            )
        remaining = remaining[: len(uploaded)]
    elif len(uploaded) > len(remaining):
        uploaded = uploaded[: len(remaining)]
    return list(zip(remaining, uploaded))


class ContextFilesResource:
    """
    Durable file uploads for modus.management.ModusManagement.

    mgmt.context.files.upload(path)               → FileUpload (presign + PUT + poll)
    mgmt.context.files.upload_dir(dir_path)        → UploadDirResult (parallel, continue-on-error)
    mgmt.context.files.create_upload_url(...)      → UploadUrlSlot
    mgmt.context.files.create_upload_urls([...])   → BulkUploadUrlsResult
    mgmt.context.files.upload_from_url(url)        → FileUpload
    mgmt.context.files.upload_from_urls([...])     → BulkUploadFromUrlsResult
    mgmt.context.files.get(upload_id)              → FileUpload
    mgmt.context.files.list()                      → Page[FileUpload]
    """

    def __init__(self, http: HttpClient, config: ModusConfig) -> None:
        self._http = http
        self._config = config

    def create_upload_url(self, *, file_name: str, content_type: str, file_size: int) -> UploadUrlSlot:
        """Get a presigned S3 PUT URL for one file.

        Args:
            file_name:    Original file name — used to build the S3 object key.
            content_type: MIME type. Allowed categories: PDF, images, text,
                          Office/OpenDocument documents, audio, and video.
            file_size:    File size in bytes. Rejected above 50MB.

        Returns:
            Presigned upload slot. PUT the raw bytes to ``upload_url`` within 15
            minutes, then poll ``get(upload_id)`` — there is no separate finalize call.
        """
        payload = {"fileName": file_name, "contentType": content_type, "fileSize": file_size}
        data = with_retry(
            lambda: invoke_operation(self._http, "ContextFilesController_uploadUrl", json_body=payload),
            self._config.max_retries,
        )
        return UploadUrlSlot.model_validate(data)

    def create_upload_urls(self, files: Sequence[UploadUrlInput]) -> BulkUploadUrlsResult:
        """Get presigned S3 PUT URLs for up to 100 files in one call.

        Args:
            files: Files to create upload slots for (max 100).

        Returns:
            Slots for every file that passed validation, plus per-index failures
            (bad MIME type, oversize) for the rest — never a partial 4xx.
        """
        _validate_bulk_size(len(files), name="files")
        data = with_retry(
            lambda: invoke_operation(
                self._http, "ContextFilesController_uploadUrls", json_body=_create_slots_payload(files)
            ),
            self._config.max_retries,
        )
        return BulkUploadUrlsResult.model_validate(data)

    def upload_from_url(self, url: str, *, file_name: Optional[str] = None) -> FileUpload:
        """Fetch one file from a URL and land it as durable context.

        Args:
            url:       Source URL to fetch (SSRF-guarded, 50MB cap, same MIME
                       allow-list as ``create_upload_url``).
            file_name: Override file name. Inferred from the URL path when omitted.

        Returns:
            File upload resource with status ``processing`` — parsing continues async.
        """
        payload: dict = {"url": url}
        if file_name is not None:
            payload["fileName"] = file_name
        data = with_retry(
            lambda: invoke_operation(self._http, "ContextFilesController_uploadFromUrl", json_body=payload),
            self._config.max_retries,
        )
        return FileUpload.model_validate(data)

    def upload_from_urls(self, urls: Sequence[UploadFromUrlInput]) -> BulkUploadFromUrlsResult:
        """Fetch up to 100 files from URLs in one call.

        Args:
            urls: URLs to fetch and upload (max 100).

        Returns:
            File upload resources for every URL that landed, plus per-index
            failures for the rest — never a partial 4xx.
        """
        _validate_bulk_size(len(urls), name="urls")
        data = with_retry(
            lambda: invoke_operation(
                self._http,
                "ContextFilesController_uploadFromUrls",
                json_body=_upload_from_urls_payload(urls),
            ),
            self._config.max_retries,
        )
        return BulkUploadFromUrlsResult.model_validate(data)

    def get(self, upload_id: str) -> FileUpload:
        """Fetch one file upload by its id.

        Args:
            upload_id: Upload id returned by ``create_upload_url`` / ``upload_from_url``.

        Returns:
            The file upload resource, including its processing ``status``.
        """
        validate_id(upload_id, name="upload_id")
        data = with_retry(
            lambda: invoke_operation(
                self._http, "ContextFilesController_get", path_params={"uploadId": upload_id}
            ),
            self._config.max_retries,
        )
        return FileUpload.model_validate(data)

    def list(self, *, page_size: int = _DEFAULT_LIST_PAGE_SIZE, page_token: Optional[str] = None) -> Page[FileUpload]:
        """List durable file uploads.

        Args:
            page_size:  Items per page (default 50).
            page_token: Opaque token from a previous page's ``next_page_token``.

        Returns:
            Page of file uploads. Uploads that only have a pending row (not yet
            landed) aren't included here — use ``get(upload_id)`` for those.
        """
        validate_page_size(page_size, max_page_size=200)
        return self._list_page(page_size, page_token)

    def _list_page(self, page_size: int, page_token: Optional[str]) -> Page[FileUpload]:
        params = aip_list_params(page_size, page_token)
        data = with_retry(
            lambda: invoke_operation(self._http, "ContextFilesController_list", query=params),
            self._config.max_retries,
        )
        return build_aip_page(data, "files", FileUpload, lambda cur: self._list_page(page_size, cur))

    def upload(
        self,
        path: Union[str, Path],
        *,
        wait_until: WaitUntil = "processing",
        poll_interval_s: float = 0.5,
        timeout_s: float = 120,
    ) -> FileUpload:
        """Upload a local file and wait for it to reach ``processing`` or ``ready``.

        Gets a presigned URL, PUTs the file bytes, then polls ``get()`` until the
        upload leaves ``pending`` (or reaches ``ready``/``failed``).

        Args:
            path:            Path to a local file.
            wait_until:      ``"processing"`` (parsing started, default) or
                              ``"ready"`` (parsing finished).
            poll_interval_s: Seconds between status polls.
            timeout_s:       Max seconds to wait before raising.

        Returns:
            The file upload resource once it reaches ``wait_until`` (or ``failed``).

        Raises:
            ModusError: if the PUT fails, or polling times out.
        """
        _validate_wait_until(wait_until)
        file_path = Path(path)
        if not file_path.is_file():
            raise ValueError(f"Not a file: {file_path}")
        slot = self.create_upload_url(
            file_name=file_path.name,
            content_type=DEFER_CONTENT_TYPE_TO_SERVER,
            file_size=file_path.stat().st_size,
        )
        content_type = _slot_content_type(slot, file_path.name)
        _put_bytes_sync(slot.upload_url, file_path.read_bytes(), content_type, _DEFAULT_PUT_TIMEOUT_S)
        return self._poll_until(
            slot.upload_id, wait_until=wait_until, poll_interval_s=poll_interval_s, timeout_s=timeout_s
        )

    def _poll_until(
        self, upload_id: str, *, wait_until: WaitUntil, poll_interval_s: float, timeout_s: float
    ) -> FileUpload:
        deadline = time.monotonic() + timeout_s
        while True:
            item = self.get(upload_id)
            status = _status_value(item)
            if _status_satisfies(status, wait_until):
                return item
            if time.monotonic() >= deadline:
                raise ModusError(
                    f"Timed out after {timeout_s}s waiting for upload {upload_id!r} to reach "
                    f"status {wait_until!r}; last status was {status!r}."
                )
            time.sleep(poll_interval_s)

    def upload_dir(
        self,
        path: Union[str, Path],
        *,
        recursive: bool = True,
        concurrency: int = 10,
        wait_until: WaitUntil = "processing",
    ) -> UploadDirResult:
        """Upload every file in a local directory.

        Walks ``path`` (skipping hidden files/directories and symlinks), pages
        through ``create_upload_urls()`` in batches of up to 100, then PUTs and
        polls each file with up to ``concurrency`` in flight at once. A failure on
        one file does not stop the others — check ``result.failed``.

        Args:
            path:        Path to a local directory.
            recursive:   Recurse into subdirectories (default ``True``).
            concurrency: Max concurrent PUT+poll operations.
            wait_until:  ``"processing"`` (default) or ``"ready"`` — same as ``upload()``.

        Returns:
            ``UploadDirResult`` with every successful ``FileUpload`` and every
            per-file failure (slot creation or PUT/poll), each tagged with its
            local path.
        """
        _validate_wait_until(wait_until)
        if concurrency < 1:
            raise ValueError(f"concurrency must be >= 1, got {concurrency!r}")
        dir_path = Path(path)
        if not dir_path.is_dir():
            raise ValueError(f"Not a directory: {dir_path}")

        uploaded: List[FileUpload] = []
        failed: List[UploadDirFailure] = []
        for batch in _chunked(_walk_files(dir_path, recursive=recursive), MAX_BULK_UPLOAD_FILES):
            slots = self._create_slots(batch, failed)
            for result in self._upload_batch(slots, wait_until, concurrency):
                if isinstance(result, UploadDirFailure):
                    failed.append(result)
                else:
                    uploaded.append(result)
        return UploadDirResult(uploaded=uploaded, failed=failed)

    def _create_slots(
        self, batch: Sequence[Path], failed: List[UploadDirFailure]
    ) -> List[_SlotAssignment]:
        readable, inputs = _slot_inputs_for_batch(batch, failed)
        if not inputs:
            return []
        result = self.create_upload_urls(inputs)
        return _assign_slots(readable, result, failed)

    def _upload_batch(
        self, slots: Sequence[_SlotAssignment], wait_until: WaitUntil, concurrency: int
    ) -> List[Union[FileUpload, UploadDirFailure]]:
        if not slots:
            return []

        def worker(entry: _SlotAssignment) -> Union[FileUpload, UploadDirFailure]:
            file_path, slot = entry
            try:
                content_type = _slot_content_type(slot, file_path.name)
                _put_bytes_sync(slot.upload_url, file_path.read_bytes(), content_type, _DEFAULT_PUT_TIMEOUT_S)
                return self._poll_until(slot.upload_id, wait_until=wait_until, poll_interval_s=0.5, timeout_s=120)
            except Exception as exc:  # continue-on-error: one bad file must not sink the batch
                return UploadDirFailure(path=str(file_path), error=str(exc))

        with ThreadPoolExecutor(max_workers=min(concurrency, len(slots))) as pool:
            return list(pool.map(worker, slots))


class AsyncContextFilesResource:
    """Async twin of ``ContextFilesResource``."""

    def __init__(self, http: AsyncHttpClient, config: ModusConfig) -> None:
        self._http = http
        self._config = config

    async def create_upload_url(self, *, file_name: str, content_type: str, file_size: int) -> UploadUrlSlot:
        """Get a presigned S3 PUT URL for one file. See the sync ``create_upload_url`` for argument details."""
        payload = {"fileName": file_name, "contentType": content_type, "fileSize": file_size}
        data = await async_with_retry(
            lambda: invoke_operation_async(self._http, "ContextFilesController_uploadUrl", json_body=payload),
            self._config.max_retries,
        )
        return UploadUrlSlot.model_validate(data)

    async def create_upload_urls(self, files: Sequence[UploadUrlInput]) -> BulkUploadUrlsResult:
        """Get presigned S3 PUT URLs for up to 100 files. See the sync ``create_upload_urls`` for argument details."""
        _validate_bulk_size(len(files), name="files")
        data = await async_with_retry(
            lambda: invoke_operation_async(
                self._http, "ContextFilesController_uploadUrls", json_body=_create_slots_payload(files)
            ),
            self._config.max_retries,
        )
        return BulkUploadUrlsResult.model_validate(data)

    async def upload_from_url(self, url: str, *, file_name: Optional[str] = None) -> FileUpload:
        """Fetch one file from a URL. See the sync ``upload_from_url`` for argument details."""
        payload: dict = {"url": url}
        if file_name is not None:
            payload["fileName"] = file_name
        data = await async_with_retry(
            lambda: invoke_operation_async(self._http, "ContextFilesController_uploadFromUrl", json_body=payload),
            self._config.max_retries,
        )
        return FileUpload.model_validate(data)

    async def upload_from_urls(self, urls: Sequence[UploadFromUrlInput]) -> BulkUploadFromUrlsResult:
        """Fetch up to 100 files from URLs. See the sync ``upload_from_urls`` for argument details."""
        _validate_bulk_size(len(urls), name="urls")
        data = await async_with_retry(
            lambda: invoke_operation_async(
                self._http,
                "ContextFilesController_uploadFromUrls",
                json_body=_upload_from_urls_payload(urls),
            ),
            self._config.max_retries,
        )
        return BulkUploadFromUrlsResult.model_validate(data)

    async def get(self, upload_id: str) -> FileUpload:
        """Fetch one file upload by its id. See the sync ``get`` for argument details."""
        validate_id(upload_id, name="upload_id")
        data = await async_with_retry(
            lambda: invoke_operation_async(
                self._http, "ContextFilesController_get", path_params={"uploadId": upload_id}
            ),
            self._config.max_retries,
        )
        return FileUpload.model_validate(data)

    async def list(
        self, *, page_size: int = _DEFAULT_LIST_PAGE_SIZE, page_token: Optional[str] = None
    ) -> AsyncPage[FileUpload]:
        """List durable file uploads. See the sync ``list`` for argument details."""
        validate_page_size(page_size, max_page_size=200)
        return await self._list_page(page_size, page_token)

    async def _list_page(self, page_size: int, page_token: Optional[str]) -> AsyncPage[FileUpload]:
        params = aip_list_params(page_size, page_token)
        data = await async_with_retry(
            lambda: invoke_operation_async(self._http, "ContextFilesController_list", query=params),
            self._config.max_retries,
        )
        return build_async_aip_page(data, "files", FileUpload, lambda cur: self._list_page(page_size, cur))

    async def upload(
        self,
        path: Union[str, Path],
        *,
        wait_until: WaitUntil = "processing",
        poll_interval_s: float = 0.5,
        timeout_s: float = 120,
    ) -> FileUpload:
        """Upload a local file and wait for processing. See the sync ``upload`` for argument details."""
        _validate_wait_until(wait_until)
        file_path = Path(path)
        if not file_path.is_file():
            raise ValueError(f"Not a file: {file_path}")
        slot = await self.create_upload_url(
            file_name=file_path.name,
            content_type=DEFER_CONTENT_TYPE_TO_SERVER,
            file_size=file_path.stat().st_size,
        )
        content_type = _slot_content_type(slot, file_path.name)
        await _put_bytes_async(slot.upload_url, file_path.read_bytes(), content_type, _DEFAULT_PUT_TIMEOUT_S)
        return await self._poll_until(
            slot.upload_id, wait_until=wait_until, poll_interval_s=poll_interval_s, timeout_s=timeout_s
        )

    async def _poll_until(
        self, upload_id: str, *, wait_until: WaitUntil, poll_interval_s: float, timeout_s: float
    ) -> FileUpload:
        deadline = time.monotonic() + timeout_s
        while True:
            item = await self.get(upload_id)
            status = _status_value(item)
            if _status_satisfies(status, wait_until):
                return item
            if time.monotonic() >= deadline:
                raise ModusError(
                    f"Timed out after {timeout_s}s waiting for upload {upload_id!r} to reach "
                    f"status {wait_until!r}; last status was {status!r}."
                )
            await asyncio.sleep(poll_interval_s)

    async def upload_dir(
        self,
        path: Union[str, Path],
        *,
        recursive: bool = True,
        concurrency: int = 10,
        wait_until: WaitUntil = "processing",
    ) -> UploadDirResult:
        """Upload every file in a local directory. See the sync ``upload_dir`` for argument details."""
        _validate_wait_until(wait_until)
        if concurrency < 1:
            raise ValueError(f"concurrency must be >= 1, got {concurrency!r}")
        dir_path = Path(path)
        if not dir_path.is_dir():
            raise ValueError(f"Not a directory: {dir_path}")

        uploaded: List[FileUpload] = []
        failed: List[UploadDirFailure] = []
        for batch in _chunked(_walk_files(dir_path, recursive=recursive), MAX_BULK_UPLOAD_FILES):
            slots = await self._create_slots(batch, failed)
            for result in await self._upload_batch(slots, wait_until, concurrency):
                if isinstance(result, UploadDirFailure):
                    failed.append(result)
                else:
                    uploaded.append(result)
        return UploadDirResult(uploaded=uploaded, failed=failed)

    async def _create_slots(
        self, batch: Sequence[Path], failed: List[UploadDirFailure]
    ) -> List[_SlotAssignment]:
        readable, inputs = _slot_inputs_for_batch(batch, failed)
        if not inputs:
            return []
        result = await self.create_upload_urls(inputs)
        return _assign_slots(readable, result, failed)

    async def _upload_batch(
        self, slots: Sequence[_SlotAssignment], wait_until: WaitUntil, concurrency: int
    ) -> List[Union[FileUpload, UploadDirFailure]]:
        if not slots:
            return []
        semaphore = asyncio.Semaphore(concurrency)

        async def worker(entry: _SlotAssignment) -> Union[FileUpload, UploadDirFailure]:
            file_path, slot = entry
            async with semaphore:
                try:
                    content_type = _slot_content_type(slot, file_path.name)
                    await _put_bytes_async(
                        slot.upload_url, file_path.read_bytes(), content_type, _DEFAULT_PUT_TIMEOUT_S
                    )
                    return await self._poll_until(
                        slot.upload_id, wait_until=wait_until, poll_interval_s=0.5, timeout_s=120
                    )
                except Exception as exc:  # continue-on-error: one bad file must not sink the batch
                    return UploadDirFailure(path=str(file_path), error=str(exc))

        return list(await asyncio.gather(*(worker(entry) for entry in slots)))
