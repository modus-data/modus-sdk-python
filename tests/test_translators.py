"""DTO parsing coverage for ScopeDto and WorkflowDto."""

from modus._generated.models import ScopeDto, WorkflowDto
from modus.types.scopes import Scope
from modus.types.workflows import Workflow

_PERMISSION = {"canManage": True, "canUse": True, "manageDenial": "not_owner"}

_ACCESS_CONFIG = {
    "visibility": "shared",
    "groupPermissions": {"__everyone__": {"use": True, "manage": True}},
    "guardrails": ["no-pii"],
    "sharedWith": [],
}

_AGENT_ACCESS_CONFIG = {
    "visibility": "shared",
    "groupPermissions": {"__everyone__": {"use": True, "manage": True}},
    "sharedWith": [],
}

_SCOPE_BASE = {
    "id": 1,
    "slug": "test-scope",
    "name": "Test Scope",
    "status": "active",
    "orgUuid": "org-uuid",
    "hasUnpublishedChanges": False,
    "activeVariationId": "var-1",
    "draftVariationId": None,
    "accessConfig": _ACCESS_CONFIG,
    "createdAt": "2026-01-01T00:00:00.000Z",
    "updatedAt": "2026-01-01T00:00:00.000Z",
    "deletedAt": None,
    **_PERMISSION,
}

_SCOPE_DETAIL = {
    **_SCOPE_BASE,
    "variation": {
        "instructions": ["Do stuff"],
        "model": "gpt-4o",
        "expectedOutput": "JSON",
        "toolset": {},
        "connectionSet": [],
        "contextSelections": [],
        "interfaces": [],
        "evaluations": [],
        "supervisionSubordinateIds": [],
        "supervisionSubordinateDescriptions": {},
    },
}

_SCOPE_LIST = {**_SCOPE_BASE, "variation": None}

_WORKFLOW_BASE = {
    "id": 2,
    "slug": "test-workflow",
    "name": "Test Workflow",
    "status": "active",
    "type": "task",
    "orgUuid": "org-uuid",
    "hasUnpublishedChanges": False,
    "isEnabled": True,
    "activeVariationId": "var-2",
    "draftVariationId": None,
    "accessConfig": _AGENT_ACCESS_CONFIG,
    "createdAt": "2026-01-01T00:00:00.000Z",
    "updatedAt": "2026-01-01T00:00:00.000Z",
    "deletedAt": None,
    **_PERMISSION,
}

_WORKFLOW_DETAIL = {
    **_WORKFLOW_BASE,
    "variation": {"agentSelection": {"agents": [], "model": "gpt-4o-mini"}},
}

_WORKFLOW_LIST = {**_WORKFLOW_BASE, "variation": None}


def test_scope_dto_detail_exposes_variation_instructions():
    public = ScopeDto.model_validate(_SCOPE_DETAIL)
    assert isinstance(public, Scope)
    assert public.variation is not None
    assert public.variation.instructions == ["Do stuff"]
    assert public.access_config.guardrails == ["no-pii"]


def test_scope_dto_list_row_has_no_variation():
    public = ScopeDto.model_validate(_SCOPE_LIST)
    assert public.variation is None
    assert public.access_config.guardrails == ["no-pii"]


def test_scope_dto_status_preserved():
    public = ScopeDto.model_validate(_SCOPE_DETAIL)
    assert public.status == "active"


def test_scope_dto_has_unpublished_changes():
    payload = {**_SCOPE_DETAIL, "hasUnpublishedChanges": True}
    assert ScopeDto.model_validate(payload).has_unpublished_changes is True


def test_workflow_dto_detail_exposes_variation():
    public = WorkflowDto.model_validate(_WORKFLOW_DETAIL)
    assert isinstance(public, Workflow)
    assert public.variation is not None
    assert public.variation.agent_selection is not None


def test_workflow_dto_list_row_has_no_variation():
    public = WorkflowDto.model_validate(_WORKFLOW_LIST)
    assert public.variation is None


def test_workflow_dto_type_preserved():
    public = WorkflowDto.model_validate(_WORKFLOW_DETAIL)
    assert public.type == "task"


def test_workflow_dto_flags():
    public = WorkflowDto.model_validate(_WORKFLOW_DETAIL)
    assert public.is_enabled is True
    assert public.has_unpublished_changes is False
