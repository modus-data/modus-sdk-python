"""
modus.management — configuration surface for the Modus SDK.

    from modus.management import ModusManagement
    mgmt = ModusManagement(api_key="modus_...")
    mgmt.skills.create(name="Analyst", model="gpt-4o")

Errors are the shared modus.* hierarchy (modus.NotFoundError, etc.).
"""

from ._client import AsyncModusManagement, ModusManagement
from .types import (
    Agent,
    AgentSelection,
    AgentSelectionEntry,
    AgentStatus,
    AgentTrigger,
    AgentTriggerValue,
    AgentType,
    AsyncPage,
    ContextItem,
    ContextItemDeletion,
    ContextItemUpdate,
    ContextType,
    Conversation,
    ConversationListItem,
    CreatedContextItem,
    JsonObject,
    ManualTrigger,
    Memory,
    MemorySearchRequest,
    MemoryUpdate,
    Message,
    Page,
    ScheduleTrigger,
    Skill,
    SkillStatus,
    Toolset,
    TriggerSchedule,
    WorkflowGraph,
)

__all__ = [
    "Agent",
    "AgentSelection",
    "AgentSelectionEntry",
    "AgentStatus",
    "AgentTrigger",
    "AgentTriggerValue",
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
    "JsonObject",
    "ManualTrigger",
    "Memory",
    "MemorySearchRequest",
    "MemoryUpdate",
    "Message",
    "ModusManagement",
    "Page",
    "ScheduleTrigger",
    "Skill",
    "SkillStatus",
    "Toolset",
    "TriggerSchedule",
    "WorkflowGraph",
]
