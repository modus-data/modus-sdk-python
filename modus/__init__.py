"""
Modus Python SDK — consumption client.

Quick start:
    import modus

    client = modus.Modus(api_key="modus_xxx")

    for skill in client.skills.list():
        print(skill.name, skill.status)

    for item in client.context.items.list():
        print(modus.context_item_label(item))

To create or configure skills, use modus.management.ModusManagement.
"""

from importlib.metadata import PackageNotFoundError
from importlib.metadata import version as _pkg_version

from ._client import AsyncModus, Modus
from ._exceptions import (
    APIConnectionError,
    AuthenticationError,
    ConflictError,
    InternalServerError,
    ModusError,
    NotFoundError,
    PermissionDeniedError,
    RateLimitError,
    RunCancelledError,
    StreamTimeoutError,
    UnprocessableError,
)
from .types import (
    Agent,
    AgentRun,
    AgentRunCreateRequest,
    AgentRunListItem,
    AgentStatus,
    AgentType,
    AsyncPage,
    CancelRunRequest,
    ChatResult,
    Connection,
    ContextItem,
    ContextType,
    Conversation,
    ConversationListItem,
    EditQueuedRunRequest,
    InterruptRunRequest,
    Message,
    ModusRunCreateRequest,
    Page,
    ResumeRunRequest,
    Skill,
    SkillContextComposition,
    SkillRunCreateRequest,
    SkillStatus,
    SuggestionEventSource,
    SuggestionEventType,
    SuggestionQuestion,
    WorkflowActionRequest,
    context_item_label,
    is_verified,
    link_title,
    link_url,
    note_body,
    note_title,
    saved_query_name,
    saved_query_sql,
)
from .types.runs import (
    AssistantContentResetEvent,
    CancelledEvent,
    DoneEvent,
    ErrorEvent,
    StreamTimeoutEvent,
    TokenEvent,
)

try:
    __version__ = _pkg_version("modus-sdk")
except PackageNotFoundError:
    __version__ = "0.0.0.dev0"

__all__ = [
    "APIConnectionError",
    "AssistantContentResetEvent",
    "Agent",
    "AgentRun",
    "AgentRunCreateRequest",
    "AgentRunListItem",
    "AgentStatus",
    "AgentType",
    "AsyncModus",
    "AsyncPage",
    "AuthenticationError",
    "CancelledEvent",
    "ChatResult",
    "ConflictError",
    "Connection",
    "CancelRunRequest",
    "ContextItem",
    "ContextType",
    "context_item_label",
    "is_verified",
    "link_title",
    "link_url",
    "note_body",
    "note_title",
    "saved_query_name",
    "saved_query_sql",
    "Conversation",
    "ConversationListItem",
    "DoneEvent",
    "EditQueuedRunRequest",
    "ErrorEvent",
    "InternalServerError",
    "InterruptRunRequest",
    "Message",
    "ModusRunCreateRequest",
    "Modus",
    "ModusError",
    "NotFoundError",
    "Page",
    "PermissionDeniedError",
    "RateLimitError",
    "ResumeRunRequest",
    "RunCancelledError",
    "Skill",
    "SkillContextComposition",
    "SkillRunCreateRequest",
    "SkillStatus",
    "SuggestionEventSource",
    "SuggestionEventType",
    "SuggestionQuestion",
    "StreamTimeoutError",
    "StreamTimeoutEvent",
    "TokenEvent",
    "UnprocessableError",
    "WorkflowActionRequest",
    "__version__",
]
