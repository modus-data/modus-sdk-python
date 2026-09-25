"""Dashboard document, version, access, element and layout types — re-exported from API DTOs."""

from __future__ import annotations

from .._generated.models import (
    DashboardAccessDto,
    DashboardDefinitionDto,
    DashboardDraftSnapshotDto,
    DashboardDto,
    DashboardElementDto,
    DashboardElementKind,
    DashboardElementLayoutDto,
    DashboardElementPatchDto,
    DashboardElementResponseDto,
    DashboardElementsListResponseDto,
    DashboardElementSummaryDto,
    DashboardGroupPermissionDto,
    DashboardLayoutElementDto,
    DashboardSharedUserDto,
    DashboardSharePermission,
    DashboardVersionDto,
    DashboardVersionKind,
    DashboardView,
    DashboardVisibility,
    PublishDashboardResponseDto,
)

Dashboard = DashboardDto
DashboardAccess = DashboardAccessDto
DashboardDefinition = DashboardDefinitionDto
DashboardDraftSnapshot = DashboardDraftSnapshotDto
DashboardElement = DashboardElementDto
DashboardElementLayout = DashboardElementLayoutDto
DashboardElementPatch = DashboardElementPatchDto
DashboardElementResult = DashboardElementResponseDto
DashboardElementsList = DashboardElementsListResponseDto
DashboardElementSummary = DashboardElementSummaryDto
DashboardGroupPermission = DashboardGroupPermissionDto
DashboardLayoutElement = DashboardLayoutElementDto
DashboardPublishResult = PublishDashboardResponseDto
DashboardSharedUser = DashboardSharedUserDto
DashboardVersion = DashboardVersionDto

__all__ = [
    "Dashboard",
    "DashboardAccess",
    "DashboardDefinition",
    "DashboardDraftSnapshot",
    "DashboardElement",
    "DashboardElementKind",
    "DashboardElementLayout",
    "DashboardElementPatch",
    "DashboardElementResult",
    "DashboardElementSummary",
    "DashboardElementsList",
    "DashboardGroupPermission",
    "DashboardLayoutElement",
    "DashboardPublishResult",
    "DashboardSharePermission",
    "DashboardSharedUser",
    "DashboardVersion",
    "DashboardVersionKind",
    "DashboardView",
    "DashboardVisibility",
]
