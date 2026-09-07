"""
Modus Python SDK — consumption client.

Quick start:
    import modus

    client = modus.Modus(api_key="modus_xxx")

    for scope in client.scopes.list():
        print(scope.name, scope.status)

    for item in client.context.items.list():
        print(modus.context_item_label(item))

To create or configure scopes, use modus.management.ModusManagement.
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
    HttpIngestedDataRequest,
    IngestedDataRequest,
    IngestedDataResponse,
    IngestedDataResponseFormat,
    IngestedDataUploadResult,
    InterruptRunRequest,
    Message,
    ModusRunCreateRequest,
    Page,
    ResumeRunRequest,
    Scope,
    ScopeStatus,
    ScopeVariation,
    Skill,
    SkillContextComposition,
    SkillRunCreateRequest,
    SkillStatus,
    SqlIngestedDataRequest,
    SuggestionEventSource,
    SuggestionEventType,
    SuggestionQuestion,
    Workflow,
    WorkflowActionRequest,
    WorkflowStatus,
    WorkflowType,
    WorkflowVariation,
    context_item_label,
    conversation_scope_id,
    conversation_skill_id,
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
    "HttpIngestedDataRequest",
    "IngestedDataRequest",
    "IngestedDataResponse",
    "IngestedDataResponseFormat",
    "IngestedDataUploadResult",
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
    "Scope",
    "ScopeStatus",
    "ScopeVariation",
    "Skill",
    "SkillContextComposition",
    "SkillRunCreateRequest",
    "SkillStatus",
    "SqlIngestedDataRequest",
    "SuggestionEventSource",
    "SuggestionEventType",
    "SuggestionQuestion",
    "StreamTimeoutError",
    "StreamTimeoutEvent",
    "TokenEvent",
    "UnprocessableError",
    "Workflow",
    "WorkflowActionRequest",
    "WorkflowStatus",
    "WorkflowType",
    "WorkflowVariation",
    "conversation_scope_id",
    "conversation_skill_id",
    "__version__",
]
