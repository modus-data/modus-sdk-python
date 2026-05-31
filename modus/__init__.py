"""
Modus Python SDK — consumption client.

Quick start:
    import modus

    client = modus.Modus(api_key="modus_xxx")

    for skill in client.skills.list():
        print(skill.name, skill.status)

    for item in client.context.items.list():
        print(item.title)

To create or configure skills, use modus.management.ModusManagement.
"""

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
    ContextItem,
    ContextType,
    Conversation,
    ConversationListItem,
    Message,
    Page,
    Skill,
    SkillContextComposition,
    SkillStatus,
)
from .types.runs import (
    CancelledEvent,
    DoneEvent,
    ErrorEvent,
    StreamTimeoutEvent,
    TokenEvent,
)

from importlib.metadata import PackageNotFoundError, version as _pkg_version

try:
    __version__ = _pkg_version("modus-sdk")
except PackageNotFoundError:
    __version__ = "0.0.0.dev0"

__all__ = [
    "Modus",
    "AsyncModus",
    "ModusError",
    "APIConnectionError",
    "AuthenticationError",
    "PermissionDeniedError",
    "NotFoundError",
    "ConflictError",
    "UnprocessableError",
    "RateLimitError",
    "InternalServerError",
    "RunCancelledError",
    "StreamTimeoutError",
    "ChatResult",
    "SkillContextComposition",
    "Skill",
    "SkillStatus",
    "Agent",
    "AgentRun",
    "AgentRunListItem",
    "AgentStatus",
    "AgentType",
    "ContextItem",
    "ContextType",
    "Conversation",
    "ConversationListItem",
    "Message",
    "Page",
    "AsyncPage",
    "TokenEvent",
    "DoneEvent",
    "ErrorEvent",
    "CancelledEvent",
    "StreamTimeoutEvent",
    "__version__",
]
