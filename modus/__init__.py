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
    AgentRunListItem,
    AgentStatus,
    AgentType,
    AsyncPage,
    ChatResult,
    Connection,
    ContextItem,
    ContextType,
    Conversation,
    ConversationListItem,
    Message,
    Page,
    Skill,
    SkillContextComposition,
    SkillStatus,
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
    "Agent",
    "AgentRun",
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
    "ErrorEvent",
    "InternalServerError",
    "Message",
    "Modus",
    "ModusError",
    "NotFoundError",
    "Page",
    "PermissionDeniedError",
    "RateLimitError",
    "RunCancelledError",
    "Skill",
    "SkillContextComposition",
    "SkillStatus",
    "StreamTimeoutError",
    "StreamTimeoutEvent",
    "TokenEvent",
    "UnprocessableError",
    "__version__",
]
