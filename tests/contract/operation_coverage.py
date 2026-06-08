"""Single source of truth: which OpenAPI operations the SDK exposes vs. omits.

Every operation in ``openapi/v1.json`` must appear here, classified as either
``WRAPPED`` (a public SDK method calls it) or ``INTERNAL`` (deliberately not
exposed, with a reason). The SDK is *not* required to mirror the API 1:1 — but
every endpoint must be a conscious decision, not an accident. The coverage test
fails when the spec gains an operation that isn't classified here, forcing a
deliberate choice.

Keep the reasons honest and client-facing-neutral; they explain *why* a public
route is intentionally absent from the SDK.
"""
from __future__ import annotations

# operationId -> short note on where/how the SDK exposes it.
WRAPPED: dict[str, str] = {
    # --- Skills ---
    "SkillsController_list": "client.skills.list() / mgmt.skills.list()",
    "SkillsController_create": "mgmt.skills.create()",
    "SkillsController_get": "client.skills.get() / mgmt.skills.get()",
    "SkillsController_update": "mgmt.skills.update()",
    "SkillsController_softDelete": "mgmt.skills.delete()",
    "SkillsController_deploy": "mgmt.skills.deploy()",
    "SkillChatController_chat": "client.skills.chat()",
    "SkillChatController_chatStream": "client.skills.chat_stream()",
    "SkillChatController_chatContinue": "client.skills.chat(thread_id=...)",
    "SkillChatController_chatContinueStream": "client.skills.chat_stream(thread_id=...)",
    "SkillContextController_compose": "client.skills.get_context()",
    "ConversationsController_list": "client.skills.conversations(id).list()",
    "ConversationsController_get": "client.skills.conversations(id).get()",
    "MemoriesController_list": "mgmt.skills.memories(id).list()",
    "MemoriesController_search": "mgmt.skills.memories(id).search()",
    "MemoriesController_update": "mgmt.skills.memories(id).update()",
    "MemoriesController_delete": "mgmt.skills.memories(id).delete()",
    # --- Agents ---
    "AgentsController_list": "client.agents.list() / mgmt.agents.list()",
    "AgentsController_create": "mgmt.agents.create()",
    "AgentsController_get": "client.agents.get() / mgmt.agents.get()",
    "AgentsController_update": "mgmt.agents.update()",
    "AgentsController_softDelete": "mgmt.agents.delete()",
    "AgentsController_deploy": "mgmt.agents.deploy()",
    "AgentChatController_chat": "client.agents.chat()",
    "AgentChatController_chatStream": "client.agents.chat_stream()",
    "AgentChatController_chatContinue": "client.agents.chat(thread_id=...)",
    "AgentChatController_chatContinueStream": "client.agents.chat_stream(thread_id=...)",
    "AutomationRunsController_list": "client.agents.runs.list()",
    "AutomationRunsController_get": "client.agents.runs.get()",
    # --- Context ---
    "ContextItemsController_list": "client.context.items.list() / mgmt...",
    "ContextItemsController_get": "client.context.items.get() / mgmt...",
    "ContextItemsController_update": "mgmt.context.items.update()",
    "ContextItemsController_delete": "mgmt.context.items.delete()",
    "ContextItemsController_lookup": "client.context.items.lookup()",
    "ContextItemsController_listValues": "client.context.items.list_values()",
    "ContextCreatorsController_createNote": "mgmt.context.create_note()",
    "ContextCreatorsController_createSavedQuery": "mgmt.context.create_saved_query()",
    "ContextCreatorsController_createLink": "mgmt.context.create_link()",
}

# operationId -> reason it is intentionally NOT exposed by the SDK.
INTERNAL: dict[str, str] = {
    # Server rejects these creator shapes (422); not usable via SDK.
    "ContextCreatorsController_createDimension": "server returns 422 — not a usable public creator",
    "ContextCreatorsController_createFact": "server returns 422 — not a usable public creator",
    "ContextCreatorsController_createMetric": "server returns 422 — not a usable public creator",
    "ContextCreatorsController_createFilter": "server returns 422 — not a usable public creator",
    # Org ownership transfer — admin workflow, app-only for now.
    "SkillsController_requestOwnershipTransfer": "org-admin ownership workflow; app-only",
    "SkillsController_cancelOwnershipTransfer": "org-admin ownership workflow; app-only",
    "SkillsController_acceptOwnershipTransfer": "org-admin ownership workflow; app-only",
    "AgentsController_requestOwnershipTransfer": "org-admin ownership workflow; app-only",
    "AgentsController_cancelOwnershipTransfer": "org-admin ownership workflow; app-only",
    "AgentsController_acceptOwnershipTransfer": "org-admin ownership workflow; app-only",
    # Soft-delete recovery — app-only recovery affordance.
    "SkillsController_undelete": "recovery affordance; app-only",
    "AgentsController_undelete": "recovery affordance; app-only",
    # Advanced/internal skill surfaces.
    "SkillsController_patchMcpConfig": "advanced MCP wiring; app-only",
    "SkillsController_getVariation": "historic variation fetch; app-only",
    # Reporting / destructive admin.
    "UsageController_list": "usage reporting; app-only (spec marks SPA-only)",
    "OrganizationController_deleteOrganization": "destructive org wipe; admin-only, not for SDK",
}
