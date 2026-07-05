"""Agent automation run types — re-exported from OpenAPI DTOs."""

from __future__ import annotations

from .._generated.models import (
    ActiveConversationRunDto,
    ActiveRunsBySessionDto,
    ActiveRunsBySessionResponseDto,
    ActiveRunsResponseDto,
    AgentRunDto,
    AutomationRunListItemDto,
    CancelRunDto,
    EditQueuedRunDto,
    GetAutomationRunResponseDto,
    InterruptRunDto,
    ListAutomationRunsResponseDto,
    ModusRunDto,
    ResumeRunDto,
    SkillRunDto,
    WorkflowActionDto,
)

AgentRunListItem = AutomationRunListItemDto
AgentRun = GetAutomationRunResponseDto
AgentRunListPage = ListAutomationRunsResponseDto
ActiveConversationRun = ActiveConversationRunDto
ActiveConversationRunListPage = ActiveRunsResponseDto
ActiveRunsBySessionRequest = ActiveRunsBySessionDto
ActiveRunsBySessionResponse = ActiveRunsBySessionResponseDto
AgentRunCreateRequest = AgentRunDto
SkillRunCreateRequest = SkillRunDto
ModusRunCreateRequest = ModusRunDto
ResumeRunRequest = ResumeRunDto
CancelRunRequest = CancelRunDto
InterruptRunRequest = InterruptRunDto
EditQueuedRunRequest = EditQueuedRunDto
WorkflowActionRequest = WorkflowActionDto

__all__ = [
    "ActiveConversationRun",
    "ActiveConversationRunDto",
    "ActiveConversationRunListPage",
    "ActiveRunsBySessionDto",
    "ActiveRunsBySessionRequest",
    "ActiveRunsBySessionResponse",
    "ActiveRunsBySessionResponseDto",
    "ActiveRunsResponseDto",
    "AgentRun",
    "AgentRunCreateRequest",
    "AgentRunListItem",
    "AgentRunListPage",
    "CancelRunRequest",
    "EditQueuedRunRequest",
    "InterruptRunRequest",
    "ModusRunCreateRequest",
    "ResumeRunRequest",
    "SkillRunCreateRequest",
    "WorkflowActionRequest",
    "AgentRunDto",
    "AutomationRunListItemDto",
    "CancelRunDto",
    "EditQueuedRunDto",
    "GetAutomationRunResponseDto",
    "InterruptRunDto",
    "ListAutomationRunsResponseDto",
    "ModusRunDto",
    "ResumeRunDto",
    "SkillRunDto",
    "WorkflowActionDto",
]
