"""Single source of truth: which OpenAPI operations the SDK exposes.

Every operation in ``openapi/v1.json`` must appear here with a note on where the
SDK method lives. Each mapped operation makes a real HTTP call.
"""
from __future__ import annotations

# operationId -> short note on where/how the SDK exposes it.
OPERATIONS: dict[str, str] = {
    # --- Skills ---
    "SkillsController_list": "client.skills.list() / mgmt.skills.list()",
    "SkillsController_create": "mgmt.skills.create()",
    "SkillsController_get": "client.skills.get() / mgmt.skills.get()",
    "SkillsController_update": "mgmt.skills.update()",
    "SkillsController_delete": "mgmt.skills.delete()",
    "SkillsController_deploy": "mgmt.skills.deploy()",
    "SkillChatController_chat": "client.skills.chat() / client.skills.chat_stream()",
    "SkillChatController_chatContinue": "client.skills.chat(thread_id=...)",
    "SkillContextController_compose": "client.skills.get_context()",
    "ConversationsController_list": "client.skills.conversations(id).list()",
    "ConversationsController_get": "client.skills.conversations(id).get()",
    "MemoriesController_list": "mgmt.skills.memories(id).list()",
    "MemoriesController_search": "mgmt.skills.memories(id).search()",
    "MemoriesController_update": "mgmt.skills.memories(id).update()",
    "MemoriesController_delete": "mgmt.skills.memories(id).delete()",
    "SkillsController_requestOwnershipTransfer": "mgmt.skills.request_ownership_transfer()",
    "SkillsController_cancelOwnershipTransfer": "mgmt.skills.cancel_ownership_transfer()",
    "SkillsController_acceptOwnershipTransfer": "mgmt.skills.accept_ownership_transfer()",
    "SkillsController_restore": "mgmt.skills.restore()",
    "SkillsController_patchMcpConfig": "mgmt.skills.patch_mcp_config()",
    "SkillsController_getVariation": "mgmt.skills.get_variation()",
    # --- Agents ---
    "AgentsController_list": "client.agents.list() / mgmt.agents.list()",
    "AgentsController_create": "mgmt.agents.create()",
    "AgentsController_get": "client.agents.get() / mgmt.agents.get()",
    "AgentsController_update": "mgmt.agents.update()",
    "AgentsController_delete": "mgmt.agents.delete()",
    "AgentsController_deploy": "mgmt.agents.deploy()",
    "AutomationRunsController_list": "client.agents.runs.list()",
    "AutomationRunsController_get": "client.agents.runs.get()",
    "AgentsController_requestOwnershipTransfer": "mgmt.agents.request_ownership_transfer()",
    "AgentsController_cancelOwnershipTransfer": "mgmt.agents.cancel_ownership_transfer()",
    "AgentsController_acceptOwnershipTransfer": "mgmt.agents.accept_ownership_transfer()",
    "AgentsController_restore": "mgmt.agents.restore()",
    # --- Context ---
    "ContextItemsController_list": "client.context.items.list() / mgmt.context.items.list()",
    "ContextItemsController_get": "client.context.items.get() / mgmt.context.items.get()",
    "ContextItemsController_update": (
        "mgmt.context.items.update(); convenience: update_note, update_link, update_saved_query"
    ),
    "ContextItemsController_delete": "mgmt.context.items.delete()",
    "ContextItemsController_lookup": "client.context.items.lookup()",
    "ContextItemsController_listValues": "client.context.items.list_values()",
    "ContextCreatorsController_createNote": "mgmt.context.create_note()",
    "ContextCreatorsController_createSavedQuery": "mgmt.context.create_saved_query()",
    "ContextCreatorsController_createLink": "mgmt.context.create_link()",
    "ContextCreatorsController_createDimension": "mgmt.context.create_dimension()",
    "ContextCreatorsController_createFact": "mgmt.context.create_fact()",
    "ContextCreatorsController_createMetric": "mgmt.context.create_metric()",
    "ContextCreatorsController_createFilter": "mgmt.context.create_filter()",
    # --- Connections ---
    "ConnectionsController_list": "client.connections.list()",
    # --- Usage ---
    "UsageController_list": "mgmt.usage.list()",
    # --- Organization ---
    "OrganizationController_deleteOrganization": "mgmt.organization.delete()",
}
