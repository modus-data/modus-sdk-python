"""
modus.management — configuration surface for the Modus SDK.

    from modus.management import ModusManagement
    mgmt = ModusManagement(api_key="modus_...")
    mgmt.skills.create(name="Analyst", model="gpt-4o")

Errors are the shared modus.* hierarchy (modus.NotFoundError, etc.).
"""

from ._client import AsyncModusManagement, ModusManagement
from .types import (
    AccessConfig,
    Agent,
    AgentStatus,
    AgentType,
    AsyncPage,
    ContextItem,
    ContextItemDeletion,
    ContextItemUpdate,
    ContextType,
    Conversation,
    ConversationListItem,
    CreatedContextItem,
    Message,
    Page,
    Skill,
    SkillStatus,
)

__all__ = [
    "AccessConfig",
    "Agent",
    "AgentStatus",
    "AgentType",
    "AsyncModusManagement",
    "AsyncPage",
    "ContextItem",
    "ContextItemDeletion",
    "ContextItemUpdate",
    "ContextType",
    "Conversation",
    "ConversationListItem",
    "CreatedContextItem",
    "Message",
    "ModusManagement",
    "Page",
    "Skill",
    "SkillStatus",
]
