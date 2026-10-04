"""Context file upload types — re-exported from OpenAPI DTOs, plus small
client-side value types for the ``upload()`` / ``upload_dir()`` helpers."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable, List, Optional, Union


@dataclass(frozen=True)
class UploadProgress:
    """Progress event fired once per file after it succeeds or fails in a batch upload."""

    completed: int
    total: int
    succeeded: int
    failed: int


UploadProgressCallback = Callable[[UploadProgress], None]

from .._generated.models import (
    BulkFinalizeResponseDto,
    BulkUploadFromUrlsResponseDto,
    BulkUploadUrlsResponseDto,
    FailedFinalizeDto,
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
BulkFinalizeResult = BulkFinalizeResponseDto
FinalizeFailure = FailedFinalizeDto


@dataclass(frozen=True)
class UploadFileInput:
    """A local file and optional folder label for ``upload_files()``."""

    path: Union[str, Path]
    folder_path: Optional[str] = None


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
    folder_path: Optional[str] = None


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
    "BulkFinalizeResult",
    "BulkUploadFromUrlsResult",
    "BulkUploadUrlsResult",
    "FailedUploadFromUrl",
    "FailedUploadUrl",
    "FileUpload",
    "FileUploadStatus",
    "FinalizeFailure",
    "FinalizeInput",
    "UploadDirFailure",
    "UploadDirResult",
    "UploadFileInput",
    "UploadFromUrlInput",
    "UploadProgress",
    "UploadProgressCallback",
    "UploadUrlInput",
    "UploadUrlSlot",
]


@dataclass(frozen=True)
class FinalizeInput:
    """One entry for ``finalize_many()``."""

    upload_id: str
    file_name: str
    folder_path: Optional[str] = None
