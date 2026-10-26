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
    FollowUpRunDto,
    GetAutomationRunResponseDto,
    InterruptRunDto,
    ListAutomationRunsResponseDto,
    ModusRunDto,
    ResumeRunDto,
    RunAdmissionResponseDto,
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
FollowUpRunRequest = FollowUpRunDto
RunAdmission = RunAdmissionResponseDto
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
    "FollowUpRunRequest",
    "InterruptRunRequest",
    "ModusRunCreateRequest",
    "ResumeRunRequest",
    "RunAdmission",
    "SkillRunCreateRequest",
    "WorkflowActionRequest",
    "AgentRunDto",
    "AutomationRunListItemDto",
    "CancelRunDto",
    "EditQueuedRunDto",
    "FollowUpRunDto",
    "GetAutomationRunResponseDto",
    "InterruptRunDto",
    "ListAutomationRunsResponseDto",
    "ModusRunDto",
    "ResumeRunDto",
    "RunAdmissionResponseDto",
    "SkillRunDto",
    "WorkflowActionDto",
]
