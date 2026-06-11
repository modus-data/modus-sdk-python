"""Agent automation run types — re-exported from OpenAPI DTOs."""

from __future__ import annotations

from .._generated.models import (
    AutomationRunListItemDto,
    GetAutomationRunResponseDto,
    ListAutomationRunsResponseDto,
)

AgentRunListItem = AutomationRunListItemDto
AgentRun = GetAutomationRunResponseDto
AgentRunListPage = ListAutomationRunsResponseDto

__all__ = [
    "AgentRun",
    "AgentRunListItem",
    "AgentRunListPage",
    "AutomationRunListItemDto",
    "GetAutomationRunResponseDto",
    "ListAutomationRunsResponseDto",
]
