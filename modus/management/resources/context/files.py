"""Context files resource — durable file uploads for modus.management."""

from __future__ import annotations

import asyncio
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Callable, Iterator, List, Literal, Optional, Sequence, Tuple, Union

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
    BulkFinalizeResult,
    BulkUploadFromUrlsResult,
    BulkUploadUrlsResult,
    FileUpload,
    FinalizeInput,
    UploadDirFailure,
    UploadDirResult,
    UploadFromUrlInput,
    UploadProgress,
    UploadProgressCallback,
    UploadUrlInput,
    UploadUrlSlot,
)

# Bulk `create_upload_urls` / `upload_from_urls` request cap — matches the backend.
MAX_BULK_UPLOAD_FILES = 100

_DEFAULT_LIST_PAGE_SIZE = 50
_DEFAULT_PUT_TIMEOUT_S = 60.0
# `pending` is gone from the public enum: an upload has no resource until it is
# finalized. Kept at rank 0 so an older server still reporting it is ordered
# below `processing` rather than treated as unknown.
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


def _finalize_payload(uploads: Sequence["FinalizeInput"]) -> dict:
    return {"uploads": [{"uploadId": u.upload_id, "fileName": u.file_name} for u in uploads]}


def _finalize_inputs_for(slots: Sequence[_SlotAssignment]) -> List["FinalizeInput"]:
    # `slot.file_name` rather than the local basename: the server sanitizes the
    # name when minting the key, and finalize re-derives the key from it.
    return [
        FinalizeInput(upload_id=slot.upload_id, file_name=slot.file_name or path.name)
        for path, slot in slots
    ]


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
            minutes, then call
            ``finalize(slot.upload_id, file_name=slot.file_name)``.

            Pass the slot's own ``file_name`` rather than your local basename:
            the server may sanitize the requested name when it mints the key,
            and finalization re-derives the key from ``upload_id`` and
            ``file_name``. Fall back to the basename only if the slot returns
            no name.
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

    def finalize(self, upload_id: str, *, file_name: str) -> FileUpload:
        """Turn a file already PUT to a presigned URL into durable context.

        Call once the PUT completes. The server locates the object from
        ``upload_id`` + ``file_name`` and validates the bytes that arrived.
        Safe to retry — a second call returns the same resource.
        """
        validate_id(upload_id, name="upload_id")
        data = with_retry(
            lambda: invoke_operation(
                self._http,
                "ContextFilesController_finalize",
                path_params={"uploadId": upload_id},
                json_body={"fileName": file_name},
            ),
            self._config.max_retries,
        )
        return FileUpload.model_validate(data)

    def finalize_many(self, uploads: Sequence[FinalizeInput]) -> BulkFinalizeResult:
        """Finalize up to 100 uploads in one call.

        What makes directory upload cheap: 2000 files cost 20 requests here
        rather than 2000. Per-index failures never fail the whole batch.
        """
        _validate_bulk_size(len(uploads), name="uploads")
        data = with_retry(
            lambda: invoke_operation(
                self._http, "ContextFilesController_finalizeMany", json_body=_finalize_payload(uploads)
            ),
            self._config.max_retries,
        )
        return BulkFinalizeResult.model_validate(data)

    def upload_files(
        self,
        paths: Sequence[Union[str, Path]],
        *,
        concurrency: int = 10,
        wait_until: WaitUntil = "processing",
        on_progress: Optional[UploadProgressCallback] = None,
    ) -> UploadDirResult:
        """Upload an explicit list of local files.

        Same machinery as ``upload_dir`` without the directory walk.

        Args:
            on_progress: Optional callback after each file settles. Receives
                cumulative ``completed``, ``total``, ``succeeded``, and ``failed``
                counts. The SDK never prints; wire this for CLI/UI progress.
        """
        return self._upload_paths(
            [Path(p) for p in paths],
            concurrency=concurrency,
            wait_until=wait_until,
            on_progress=on_progress,
        )

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
        # Finalize returns the resource already at `processing`, so it replaces
        # the first poll rather than adding a round trip.
        finalized = self.finalize(slot.upload_id, file_name=slot.file_name or file_path.name)
        if _status_satisfies(_status_value(finalized), wait_until):
            return finalized
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
        on_progress: Optional[UploadProgressCallback] = None,
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
            on_progress: Optional callback after each file settles. Receives
                cumulative ``completed``, ``total``, ``succeeded``, and ``failed``
                counts. The SDK never prints; wire this for CLI/UI progress.

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

        return self._upload_paths(
            _walk_files(dir_path, recursive=recursive),
            concurrency=concurrency,
            wait_until=wait_until,
            on_progress=on_progress,
        )

    def _upload_paths(
        self,
        files: Sequence[Path],
        *,
        concurrency: int,
        wait_until: WaitUntil,
        on_progress: Optional[UploadProgressCallback] = None,
    ) -> UploadDirResult:
        """Shared body of ``upload_files`` and ``upload_dir``."""
        _validate_wait_until(wait_until)
        if concurrency < 1:
            raise ValueError(f"concurrency must be >= 1, got {concurrency!r}")
        uploaded: List[FileUpload] = []
        failed: List[UploadDirFailure] = []
        total = len(files)
        completed = 0

        def emit() -> None:
            nonlocal completed
            completed += 1
            if on_progress is not None:
                on_progress(
                    UploadProgress(
                        completed=completed,
                        total=total,
                        succeeded=len(uploaded),
                        failed=len(failed),
                    )
                )

        for batch in _chunked(list(files), MAX_BULK_UPLOAD_FILES):
            failed_before = len(failed)
            slots = self._create_slots(batch, failed)
            # create_upload_urls can report several failures in one synchronous call,
            # so tick `failed` up one at a time here — reusing `emit()` would report
            # the final `len(failed)` on every tick and break the
            # completed == succeeded + failed invariant for all but the last of them.
            for reported in range(failed_before + 1, len(failed) + 1):
                completed += 1
                if on_progress is not None:
                    on_progress(
                        UploadProgress(
                            completed=completed,
                            total=total,
                            succeeded=len(uploaded),
                            failed=reported,
                        )
                    )

            def on_outcome(result: Union[FileUpload, UploadDirFailure]) -> None:
                if isinstance(result, UploadDirFailure):
                    failed.append(result)
                else:
                    uploaded.append(result)
                emit()

            self._upload_batch(slots, wait_until, concurrency, on_outcome=on_outcome)
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
        self,
        slots: Sequence[_SlotAssignment],
        wait_until: WaitUntil,
        concurrency: int,
        *,
        on_outcome: Optional[Callable[[Union[FileUpload, UploadDirFailure]], None]] = None,
    ) -> List[Union[FileUpload, UploadDirFailure]]:
        if not slots:
            return []

        out: List[Union[FileUpload, UploadDirFailure]] = []

        def put(entry: _SlotAssignment) -> Union[_SlotAssignment, UploadDirFailure]:
            file_path, slot = entry
            try:
                content_type = _slot_content_type(slot, file_path.name)
                _put_bytes_sync(slot.upload_url, file_path.read_bytes(), content_type, _DEFAULT_PUT_TIMEOUT_S)
                return entry
            except Exception as exc:  # continue-on-error: one bad file must not sink the batch
                return UploadDirFailure(path=str(file_path), error=str(exc))

        landed: List[_SlotAssignment] = []
        with ThreadPoolExecutor(max_workers=min(concurrency, len(slots))) as pool:
            futures = [pool.submit(put, entry) for entry in slots]
            for fut in as_completed(futures):
                result = fut.result()
                if isinstance(result, UploadDirFailure):
                    out.append(result)
                    if on_outcome is not None:
                        on_outcome(result)
            # Preserve submit order for finalize index mapping.
            for fut in futures:
                result = fut.result()
                if not isinstance(result, UploadDirFailure):
                    landed.append(result)
        if not landed:
            return out

        # One bulk finalize for the batch — the reason a 2000-file directory
        # costs one request per 100 files rather than one per file.
        finalized = self.finalize_many(_finalize_inputs_for(landed))
        failed_indices = {int(f.index) for f in finalized.failed}
        for f in finalized.failed:
            failure = UploadDirFailure(path=str(landed[int(f.index)][0]), error=f.error)
            out.append(failure)
            if on_outcome is not None:
                on_outcome(failure)
        remaining = [entry for i, entry in enumerate(landed) if i not in failed_indices]

        if wait_until != "ready":
            for success in finalized.finalized:
                out.append(success)
                if on_outcome is not None:
                    on_outcome(success)
            return out

        # Only `ready` needs polling; `processing` is already satisfied above.
        def poll(entry: _SlotAssignment) -> Union[FileUpload, UploadDirFailure]:
            file_path, slot = entry
            try:
                return self._poll_until(slot.upload_id, wait_until=wait_until, poll_interval_s=0.5, timeout_s=120)
            except Exception as exc:
                return UploadDirFailure(path=str(file_path), error=str(exc))

        if remaining:
            with ThreadPoolExecutor(max_workers=min(concurrency, len(remaining))) as pool:
                for outcome in pool.map(poll, remaining):
                    out.append(outcome)
                    if on_outcome is not None:
                        on_outcome(outcome)
        return out


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

    async def finalize(self, upload_id: str, *, file_name: str) -> FileUpload:
        """Async twin of the sync ``finalize``."""
        validate_id(upload_id, name="upload_id")
        data = await async_with_retry(
            lambda: invoke_operation_async(
                self._http,
                "ContextFilesController_finalize",
                path_params={"uploadId": upload_id},
                json_body={"fileName": file_name},
            ),
            self._config.max_retries,
        )
        return FileUpload.model_validate(data)

    async def finalize_many(self, uploads: Sequence[FinalizeInput]) -> BulkFinalizeResult:
        """Async twin of the sync ``finalize_many``."""
        _validate_bulk_size(len(uploads), name="uploads")
        data = await async_with_retry(
            lambda: invoke_operation_async(
                self._http, "ContextFilesController_finalizeMany", json_body=_finalize_payload(uploads)
            ),
            self._config.max_retries,
        )
        return BulkFinalizeResult.model_validate(data)

    async def upload_files(
        self,
        paths: Sequence[Union[str, Path]],
        *,
        concurrency: int = 10,
        wait_until: WaitUntil = "processing",
        on_progress: Optional[UploadProgressCallback] = None,
    ) -> UploadDirResult:
        """Async twin of the sync ``upload_files``.

        Args:
            on_progress: Optional callback after each file settles. Receives
                cumulative ``completed``, ``total``, ``succeeded``, and ``failed``
                counts. The SDK never prints; wire this for CLI/UI progress.
        """
        return await self._upload_paths(
            [Path(p) for p in paths],
            concurrency=concurrency,
            wait_until=wait_until,
            on_progress=on_progress,
        )

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
        finalized = await self.finalize(slot.upload_id, file_name=slot.file_name or file_path.name)
        if _status_satisfies(_status_value(finalized), wait_until):
            return finalized
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
        on_progress: Optional[UploadProgressCallback] = None,
    ) -> UploadDirResult:
        """Upload every file in a local directory. See the sync ``upload_dir`` for argument details.

        Args:
            on_progress: Optional callback after each file settles. Receives
                cumulative ``completed``, ``total``, ``succeeded``, and ``failed``
                counts. The SDK never prints; wire this for CLI/UI progress.
        """
        _validate_wait_until(wait_until)
        if concurrency < 1:
            raise ValueError(f"concurrency must be >= 1, got {concurrency!r}")
        dir_path = Path(path)
        if not dir_path.is_dir():
            raise ValueError(f"Not a directory: {dir_path}")

        return await self._upload_paths(
            _walk_files(dir_path, recursive=recursive),
            concurrency=concurrency,
            wait_until=wait_until,
            on_progress=on_progress,
        )

    async def _upload_paths(
        self,
        files: Sequence[Path],
        *,
        concurrency: int,
        wait_until: WaitUntil,
        on_progress: Optional[UploadProgressCallback] = None,
    ) -> UploadDirResult:
        """Shared body of ``upload_files`` and ``upload_dir``."""
        _validate_wait_until(wait_until)
        if concurrency < 1:
            raise ValueError(f"concurrency must be >= 1, got {concurrency!r}")
        uploaded: List[FileUpload] = []
        failed: List[UploadDirFailure] = []
        total = len(files)
        completed = 0

        def emit() -> None:
            nonlocal completed
            completed += 1
            if on_progress is not None:
                on_progress(
                    UploadProgress(
                        completed=completed,
                        total=total,
                        succeeded=len(uploaded),
                        failed=len(failed),
                    )
                )

        for batch in _chunked(list(files), MAX_BULK_UPLOAD_FILES):
            failed_before = len(failed)
            slots = await self._create_slots(batch, failed)
            # create_upload_urls can report several failures in one synchronous call,
            # so tick `failed` up one at a time here — reusing `emit()` would report
            # the final `len(failed)` on every tick and break the
            # completed == succeeded + failed invariant for all but the last of them.
            for reported in range(failed_before + 1, len(failed) + 1):
                completed += 1
                if on_progress is not None:
                    on_progress(
                        UploadProgress(
                            completed=completed,
                            total=total,
                            succeeded=len(uploaded),
                            failed=reported,
                        )
                    )

            def on_outcome(result: Union[FileUpload, UploadDirFailure]) -> None:
                if isinstance(result, UploadDirFailure):
                    failed.append(result)
                else:
                    uploaded.append(result)
                emit()

            await self._upload_batch(slots, wait_until, concurrency, on_outcome=on_outcome)
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
        self,
        slots: Sequence[_SlotAssignment],
        wait_until: WaitUntil,
        concurrency: int,
        *,
        on_outcome: Optional[Callable[[Union[FileUpload, UploadDirFailure]], None]] = None,
    ) -> List[Union[FileUpload, UploadDirFailure]]:
        if not slots:
            return []
        semaphore = asyncio.Semaphore(concurrency)
        out: List[Union[FileUpload, UploadDirFailure]] = []

        async def put(entry: _SlotAssignment) -> Union[_SlotAssignment, UploadDirFailure]:
            file_path, slot = entry
            async with semaphore:
                try:
                    content_type = _slot_content_type(slot, file_path.name)
                    await _put_bytes_async(
                        slot.upload_url, file_path.read_bytes(), content_type, _DEFAULT_PUT_TIMEOUT_S
                    )
                    return entry
                except Exception as exc:  # continue-on-error: one bad file must not sink the batch
                    return UploadDirFailure(path=str(file_path), error=str(exc))

        tasks = [asyncio.create_task(put(entry)) for entry in slots]
        landed: List[_SlotAssignment] = []
        for fut in asyncio.as_completed(tasks):
            result = await fut
            if isinstance(result, UploadDirFailure):
                out.append(result)
                if on_outcome is not None:
                    on_outcome(result)
        for task in tasks:
            result = task.result()
            if not isinstance(result, UploadDirFailure):
                landed.append(result)
        if not landed:
            return out

        # One bulk finalize for the batch — the reason a 2000-file directory
        # costs one request per 100 files rather than one per file.
        finalized = await self.finalize_many(_finalize_inputs_for(landed))
        failed_indices = {int(f.index) for f in finalized.failed}
        for f in finalized.failed:
            failure = UploadDirFailure(path=str(landed[int(f.index)][0]), error=f.error)
            out.append(failure)
            if on_outcome is not None:
                on_outcome(failure)
        remaining = [entry for i, entry in enumerate(landed) if i not in failed_indices]

        if wait_until != "ready":
            for success in finalized.finalized:
                out.append(success)
                if on_outcome is not None:
                    on_outcome(success)
            return out

        # Only `ready` needs polling; `processing` is already satisfied above.
        async def poll(entry: _SlotAssignment) -> Union[FileUpload, UploadDirFailure]:
            file_path, slot = entry
            async with semaphore:
                try:
                    return await self._poll_until(
                        slot.upload_id, wait_until=wait_until, poll_interval_s=0.5, timeout_s=120
                    )
                except Exception as exc:
                    return UploadDirFailure(path=str(file_path), error=str(exc))

        if remaining:
            for outcome in await asyncio.gather(*(poll(entry) for entry in remaining)):
                out.append(outcome)
                if on_outcome is not None:
                    on_outcome(outcome)
        return out
