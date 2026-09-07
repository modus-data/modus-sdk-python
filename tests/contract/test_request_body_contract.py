"""Write-direction alignment: the SDK must never send a body field the API rejects.

For every write endpoint, the set of fields the SDK *can* put in the request body
must be a subset of the fields the OpenAPI request schema allows. The backend uses
a strict allow-list (``forbidNonWhitelisted``), so an extra field is a hard 400 for
every caller.

This is the test that would have caught ``context.items.update`` sending ``title``
and ``verificationStatus`` (both rejected by the server).
"""

from __future__ import annotations

from typing import Dict, Set, Type

import pytest
from modus._generated.models import (
    ActiveRunsBySessionDto,
    AgentRunDto,
    BatchCreateCustomContextItemRelationsDto,
    BatchCreateCustomContextItemsDto,
    CancelRunDto,
    ComposeSkillContextRequestDto,
    CreateCustomContextItemDto,
    EditQueuedRunDto,
    InterruptRunDto,
    ModusChatRequestDto,
    ModusContextRequestDto,
    ModusRunDto,
    ResumeRunDto,
    SkillChatRequestDto,
    SkillRunDto,
    UpdateCustomContextItemDto,
    UpdateEvaluationConfigDto,
    WorkflowActionDto,
)
from modus.management.resources.scopes._update_body import (
    _ScopeCreateBody,
    _ScopeUpdateBody,
)
from modus.management.resources.workflows._update_body import (
    _WorkflowCreateBody,
    _WorkflowUpdateBody,
)
from modus.management.types.context import ContextItemUpdate
from modus.management.types.memories import MemorySearchRequest, MemoryUpdate
from pydantic import BaseModel

_HTTP_METHODS = {"get", "post", "put", "patch", "delete"}


def _model_wire_fields(model: Type[BaseModel]) -> Set[str]:
    """Wire-level (aliased) field names the model serializes to."""
    return set(model.model_json_schema(by_alias=True).get("properties", {}).keys())


# operationId -> the field names the SDK may send in the request body.
# Model-backed bodies are derived from the model; inline-dict bodies are listed
# explicitly (these mirror exactly what the resource method can put on the wire).
SDK_REQUEST_BODY_FIELDS: Dict[str, Set[str]] = {
    "IngestedDataController_upload": {"integration_type", "request", "response"},
    "ContextItemsController_update": _model_wire_fields(ContextItemUpdate),
    "ModusChatController_chat": _model_wire_fields(ModusChatRequestDto),
    "ModusContextController_compose": _model_wire_fields(ModusContextRequestDto),
    "SuggestionsController_recordEvent": {
        "eventType",
        "source",
        "skillId",
        "threadId",
        "metadata",
    },
    "ModusRunsController_create": _model_wire_fields(ModusRunDto),
    "ResumeRunsController_create": _model_wire_fields(ResumeRunDto),
    "RunLifecycleController_activeBySession": _model_wire_fields(
        ActiveRunsBySessionDto
    ),
    "RunLifecycleController_cancel": _model_wire_fields(CancelRunDto),
    "RunLifecycleController_interrupt": _model_wire_fields(InterruptRunDto),
    "RunLifecycleController_editQueued": _model_wire_fields(EditQueuedRunDto),
    "WorkflowActionsController_execute": _model_wire_fields(WorkflowActionDto),
    "WorkflowActionsController_cancel": _model_wire_fields(CancelRunDto),
    "ContextItemsController_lookup": {"contextType", "dataPath", "contentProjection"},
    "ContextCreatorsController_createNote": {"title", "content"},
    "ContextCreatorsController_createSavedQuery": {
        "name",
        "connectionId",
        "query",
        "description",
        "path",
    },
    "ContextCreatorsController_createLink": {"url", "title", "isCrawl", "pageLimit"},
    "CustomContextItemsController_create": _model_wire_fields(
        CreateCustomContextItemDto
    ),
    "CustomContextItemsController_batchCreate": _model_wire_fields(
        BatchCreateCustomContextItemsDto
    ),
    "CustomContextItemsController_createRelations": _model_wire_fields(
        BatchCreateCustomContextItemRelationsDto
    ),
    "CustomContextItemsController_update": _model_wire_fields(
        UpdateCustomContextItemDto
    ),
    "ContextFilesController_finalize": {"fileName"},
    "ContextFilesController_finalizeMany": {"uploads"},
    "ContextFilesController_uploadUrl": {"fileName", "contentType", "fileSize"},
    "ContextFilesController_uploadUrls": {"files"},
    "ContextFilesController_uploadFromUrl": {"url", "fileName"},
    "ContextFilesController_uploadFromUrls": {"urls"},
    # --- Scopes (/api/v1/scopes; request schemas share the generated *Skill* DTOs) ---
    "ScopesController_create": _model_wire_fields(_ScopeCreateBody),
    "ScopesController_update": _model_wire_fields(_ScopeUpdateBody),
    "ScopeChatController_chat": _model_wire_fields(SkillChatRequestDto),
    "ScopeContextController_compose": _model_wire_fields(ComposeSkillContextRequestDto),
    "ScopeMemoriesController_search": _model_wire_fields(MemorySearchRequest),
    "ScopeMemoriesController_update": _model_wire_fields(MemoryUpdate),
    "EvaluationsController_updateConfig": _model_wire_fields(UpdateEvaluationConfigDto),
    "ScopeRunsController_create": _model_wire_fields(SkillRunDto),
    "ScopeSupervisionController_set": {"subordinateAgentIds"},
    "ScopeSupervisionController_setActive": {"subordinateAgentIds"},
    "ScopesController_requestOwnershipTransfer": {"newOwnerUserId"},
    "ScopesController_patchMcpConfig": {"config"},
    # Deploy takes an optional body; the SDK sends none (empty body), which the
    # server accepts. Registered explicitly so the contract guard stays honest.
    "ScopesController_deploy": set(),
    # --- Workflows (/api/v1/workflows; request schemas share the generated *Agent* DTOs) ---
    "WorkflowsController_create": _model_wire_fields(_WorkflowCreateBody),
    "WorkflowsController_update": _model_wire_fields(_WorkflowUpdateBody),
    "WorkflowRunsController_create": _model_wire_fields(AgentRunDto),
    "WorkflowsController_toggle": {"active"},
    "WorkflowInterfacesController_add": {"type", "name", "config"},
    "WorkflowInterfacesController_update": {"name", "config"},
    "WorkflowsController_requestOwnershipTransfer": {"newOwnerUserId"},
    "WorkflowsController_deploy": set(),
}


def _resolve(openapi: dict, node: dict) -> dict:
    if "$ref" in node:
        target: object = openapi
        for part in node["$ref"].lstrip("#/").split("/"):
            target = target[part]  # type: ignore[index]
        return target  # type: ignore[return-value]
    return node


def _schema_properties(openapi: dict, schema: dict) -> Set[str]:
    """Collect property names from a schema, recursing through composed refs."""
    schema = _resolve(openapi, schema)
    props: Set[str] = set(schema.get("properties", {}).keys())
    for combinator in ("allOf", "anyOf", "oneOf"):
        for sub in schema.get(combinator, []):
            props |= _schema_properties(openapi, sub)
    return props


def _request_body_properties(openapi: dict, operation_id: str) -> Set[str]:
    for path_item in openapi.get("paths", {}).values():
        for method, op in path_item.items():
            if method not in _HTTP_METHODS or not isinstance(op, dict):
                continue
            if op.get("operationId") != operation_id:
                continue
            rb = op.get("requestBody")
            if not rb:
                return set()
            rb = _resolve(openapi, rb)
            props: Set[str] = set()
            for media in rb.get("content", {}).values():
                props |= _schema_properties(openapi, media.get("schema", {}))
            return props
    raise AssertionError(f"operationId {operation_id!r} not found in spec")


@pytest.mark.parametrize("operation_id", sorted(SDK_REQUEST_BODY_FIELDS))
def test_sdk_request_body_is_subset_of_spec(openapi: dict, operation_id: str) -> None:
    sdk_fields = SDK_REQUEST_BODY_FIELDS[operation_id]
    spec_fields = _request_body_properties(openapi, operation_id)
    extra = sdk_fields - spec_fields
    assert not extra, (
        f"{operation_id}: the SDK can send fields the API does not accept "
        f"(the server rejects unknown fields with 400): {sorted(extra)}.\n"
        f"Allowed by spec: {sorted(spec_fields)}"
    )


def test_every_mapped_write_endpoint_has_a_body_contract(openapi: dict) -> None:
    # Keep this registry honest: if we map a new write endpoint, force a body check.
    from .operation_coverage import OPERATIONS

    def _has_request_body(operation_id: str) -> bool:
        for path_item in openapi.get("paths", {}).values():
            for method, op in path_item.items():
                if (
                    method in _HTTP_METHODS
                    and isinstance(op, dict)
                    and op.get("operationId") == operation_id
                ):
                    return bool(op.get("requestBody"))
        return False

    # Chat-continue / stream variants reuse the same body as their base operation.
    reuses_base_body = {
        "ModusChatController_chatStream",
        "ModusChatController_chatContinue",
        "ModusChatController_chatContinueStream",
        "ScopeChatController_chatContinue",
        "ScopeChatController_chatStream",
        "ScopeChatController_chatContinueStream",
    }
    missing = {
        oid
        for oid in OPERATIONS
        if _has_request_body(oid)
        and oid not in SDK_REQUEST_BODY_FIELDS
        and oid not in reuses_base_body
    }
    assert not missing, (
        "Mapped write endpoints without a body contract in SDK_REQUEST_BODY_FIELDS: "
        f"{sorted(missing)}"
    )
