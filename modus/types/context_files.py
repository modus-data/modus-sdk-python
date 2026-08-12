"""Context file upload types — re-exported from OpenAPI DTOs, plus small
client-side value types for the ``upload()`` / ``upload_dir()`` helpers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from .._generated.models import (
    BulkUploadFromUrlsResponseDto,
    BulkUploadUrlsResponseDto,
    FailedUploadFromUrlDto,
    FailedUploadUrlDto,
    FileUploadResourceDto,
    FileUploadResourceStatus,
    UploadUrlResponseDto,
)

FileUpload = FileUploadResourceDto
FileUploadStatus = FileUploadResourceStatus
UploadUrlSlot = UploadUrlResponseDto
BulkUploadUrlsResult = BulkUploadUrlsResponseDto
BulkUploadFromUrlsResult = BulkUploadFromUrlsResponseDto
FailedUploadUrl = FailedUploadUrlDto
FailedUploadFromUrl = FailedUploadFromUrlDto


@dataclass(frozen=True)
class UploadUrlInput:
    """One file entry for ``create_upload_urls()``."""

    file_name: str
    content_type: str
    file_size: int


@dataclass(frozen=True)
class UploadFromUrlInput:
    """One URL entry for ``upload_from_urls()``."""

    url: str
    file_name: Optional[str] = None


@dataclass(frozen=True)
class UploadDirFailure:
    """A single file that failed during ``upload_dir()`` (slot creation or PUT)."""

    path: str
    error: str


@dataclass(frozen=True)
class UploadDirResult:
    """Outcome of ``upload_dir()`` — successes and per-file failures."""

    uploaded: List[FileUpload]
    failed: List[UploadDirFailure]


__all__ = [
    "BulkUploadFromUrlsResult",
    "BulkUploadUrlsResult",
    "FailedUploadFromUrl",
    "FailedUploadUrl",
    "FileUpload",
    "FileUploadStatus",
    "UploadDirFailure",
    "UploadDirResult",
    "UploadFromUrlInput",
    "UploadUrlInput",
    "UploadUrlSlot",
]
