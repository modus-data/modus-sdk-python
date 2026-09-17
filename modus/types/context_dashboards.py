"""Dashboard draft element and layout types — re-exported from API DTOs."""

from __future__ import annotations

from .._generated.models import (
    DashboardDto,
    DashboardElementDto,
    DashboardElementKind,
    DashboardElementLayoutDto,
    DashboardElementPatchDto,
    DashboardElementResponseDto,
    DashboardElementsListResponseDto,
    DashboardElementSummaryDto,
    DashboardLayoutElementDto,
)

Dashboard = DashboardDto
DashboardElement = DashboardElementDto
DashboardElementLayout = DashboardElementLayoutDto
DashboardElementPatch = DashboardElementPatchDto
DashboardElementResult = DashboardElementResponseDto
DashboardElementsList = DashboardElementsListResponseDto
DashboardElementSummary = DashboardElementSummaryDto
DashboardLayoutElement = DashboardLayoutElementDto

__all__ = [
    "Dashboard",
    "DashboardElement",
    "DashboardElementKind",
    "DashboardElementLayout",
    "DashboardElementPatch",
    "DashboardElementResult",
    "DashboardElementSummary",
    "DashboardElementsList",
    "DashboardLayoutElement",
]
