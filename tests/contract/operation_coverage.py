"""Single source of truth: which OpenAPI operations the SDK exposes.

Every operation in the public OpenAPI snapshot must appear here with a note on
where the SDK method lives. Each mapped operation makes a real HTTP call.
"""
from __future__ import annotations

# operationId -> short note on where/how the SDK exposes it.
OPERATIONS: dict[str, str] = {
    # --- Scopes (/api/v1/scopes) ---
    "ScopesController_list": "client.scopes.list() / mgmt.scopes.list()",
    "ScopesController_create": "mgmt.scopes.create()",
    "ScopesController_get": "client.scopes.get() / mgmt.scopes.get()",
    "ScopesController_update": "mgmt.scopes.update()",
    "ScopesController_delete": "mgmt.scopes.delete()",
    "ScopesController_deploy": "mgmt.scopes.deploy()",
    "ScopesController_restore": "mgmt.scopes.restore()",
    "ScopesController_getVariation": "mgmt.scopes.get_variation()",
    "ScopesController_patchMcpConfig": "mgmt.scopes.patch_mcp_config()",
    "ScopesController_requestOwnershipTransfer": "mgmt.scopes.request_ownership_transfer()",
    "ScopesController_cancelOwnershipTransfer": "mgmt.scopes.cancel_ownership_transfer()",
    "ScopesController_acceptOwnershipTransfer": "mgmt.scopes.accept_ownership_transfer()",
    "ScopeChatController_chat": "client.scopes.chat()",
    "ScopeChatController_chatContinue": "client.scopes.chat(thread_id=...)",
    "ScopeContextController_compose": "client.scopes.get_context()",
    "ScopeConversationsController_list": "client.scopes.conversations(id).list()",
    "ScopeConversationsController_get": "client.scopes.conversations(id).get()",
    "ScopeMemoriesController_list": "mgmt.scopes.memories(id).list()",
    "ScopeMemoriesController_search": "mgmt.scopes.memories(id).search()",
    "ScopeMemoriesController_update": "mgmt.scopes.memories(id).update()",
    "ScopeMemoriesController_delete": "mgmt.scopes.memories(id).delete()",
    "EvaluationsController_getConfig": "mgmt.scopes.evaluations(id).get_config()",
    "EvaluationsController_updateConfig": "mgmt.scopes.evaluations(id).update_config()",
    "EvaluationsController_triggerRun": "mgmt.scopes.evaluations(id).trigger_run()",
    "EvaluationsController_listRuns": "mgmt.scopes.evaluations(id).list_runs()",
    "EvaluationsController_getRun": "mgmt.scopes.evaluations(id).get_run(run_id)",
    "ScopeRunsController_create": "client.workflows.runs.create_scope(scope_id, body)",
    # --- Workflows (/api/v1/workflows) ---
    "WorkflowsController_list": "client.workflows.list() / mgmt.workflows.list()",
    "WorkflowsController_create": "mgmt.workflows.create()",
    "WorkflowsController_get": "client.workflows.get() / mgmt.workflows.get()",
    "WorkflowsController_update": "mgmt.workflows.update()",
    "WorkflowsController_delete": "mgmt.workflows.delete()",
    "WorkflowsController_deploy": "mgmt.workflows.deploy()",
    "WorkflowsController_restore": "mgmt.workflows.restore()",
    "WorkflowsController_requestOwnershipTransfer": "mgmt.workflows.request_ownership_transfer()",
    "WorkflowsController_cancelOwnershipTransfer": "mgmt.workflows.cancel_ownership_transfer()",
    "WorkflowsController_acceptOwnershipTransfer": "mgmt.workflows.accept_ownership_transfer()",
    "WorkflowRunsController_list": "client.workflows.runs.list()",
    "WorkflowRunsController_get": "client.workflows.runs.get()",
    "WorkflowRunsController_create": "client.workflows.runs.create(workflow_id, body)",
    # --- Run lifecycle / streaming (agent-service) ---
    "ModusRunsController_create": "client.workflows.runs.create_modus()",
    "ResumeRunsController_create": "client.workflows.runs.resume()",
    "RunLifecycleController_active": "client.workflows.runs.active()",
    "RunLifecycleController_activeBySession": "client.workflows.runs.active_by_session()",
    "RunLifecycleController_cancel": "client.workflows.runs.cancel()",
    "RunLifecycleController_events": "client.workflows.runs.events()",
    "RunLifecycleController_interrupt": "client.workflows.runs.interrupt()",
    "RunLifecycleController_editQueued": "client.workflows.runs.edit_queued()",
    "RunLifecycleController_stream": "client.workflows.runs.stream()",
    "WorkflowActionsController_execute": "client.workflows.workflow_actions.execute()",
    "WorkflowActionsController_cancel": "client.workflows.workflow_actions.cancel()",
    # --- Modus (native org assistant) ---
    "ModusChatController_chat": "client.modus.chat()",
    "ModusChatController_chatContinue": "client.modus.chat(thread_id=...)",
    "ModusContextController_compose": "client.modus.get_context()",
    "ModusConversationsController_list": "client.modus.conversations.list()",
    "ModusConversationsController_get": "client.modus.conversations.get()",
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
    "CustomContextItemsController_list": "client.context.custom_items.list() / mgmt.context.custom_items.list()",
    "CustomContextItemsController_get": "client.context.custom_items.get() / mgmt.context.custom_items.get()",
    "CustomContextItemsController_create": "mgmt.context.custom_items.create()",
    "CustomContextItemsController_batchCreate": "mgmt.context.custom_items.batch_create()",
    "CustomContextItemsController_update": "mgmt.context.custom_items.update()",
    "CustomContextItemsController_delete": "mgmt.context.custom_items.delete()",
    # --- Connections ---
    "ConnectionsController_list": "client.connections.list()",
    # --- Suggestions ---
    "SuggestionsController_listApproved": "client.suggestions.list()",
    "SuggestionsController_recordEvent": "client.suggestions.record_event()",
    # --- Usage ---
    "UsageController_list": "mgmt.usage.list()",
    # --- Organization ---
    "OrganizationController_deleteOrganization": "mgmt.organization.delete()",
}
