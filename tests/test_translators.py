"""DTO parsing coverage for ScopeDto and WorkflowDto."""

import pytest
from modus._generated.models import PatchSkillMcpConfigResponseDto, ScopeDto, WorkflowDto
from modus.types.scopes import Scope
from modus.types.workflows import Workflow
from pydantic import ValidationError

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


def test_backfilled_scope_interface_decodes_and_sparse_rows_do_not():
    """GET after the historical backfill has id, name, and config. A sparse row does not."""
    backfilled = {
        "id": "mcp-1",
        "type": "mcp",
        "name": "MCP Server",
        "config": {"coreTools": {"chat": False, "getContext": True, "teachModus": False}},
    }
    payload = {
        **_SCOPE_DETAIL,
        "variation": {**_SCOPE_DETAIL["variation"], "interfaces": [backfilled]},
    }
    parsed = ScopeDto.model_validate(payload)
    assert parsed.variation is not None
    row = parsed.variation.interfaces[0]
    assert row.id == "mcp-1"
    assert row.name == "MCP Server"
    assert row.type == "mcp"
    assert row.config.core_tools is not None
    assert row.config.core_tools.model_dump(by_alias=True) == {
        "chat": False,
        "getContext": True,
        "teachModus": False,
    }

    for sparse in (
        [{"type": "mcp"}],
        [{"id": "mcp-1", "type": "mcp", "name": "MCP Server"}],
    ):
        bad = {
            **_SCOPE_DETAIL,
            "variation": {**_SCOPE_DETAIL["variation"], "interfaces": sparse},
        }
        with pytest.raises(ValidationError):
            ScopeDto.model_validate(bad)


def _scope_with_config(config: dict) -> dict:
    return {
        **_SCOPE_DETAIL,
        "variation": {**_SCOPE_DETAIL["variation"], "interfaces": [{
            "id": "mcp-1",
            "type": "mcp",
            "name": "MCP Server",
            "config": config,
        }]},
    }


def test_effective_mcp_config_responses_decode_and_round_trip():
    """Responses return the effective config, including for slices that were stored malformed."""
    core = {"chat": False, "getContext": True, "teachModus": False}
    exposure = {"version": 1, "mode": "discovery", "allowedIntegrationKeys": []}
    # Stored [], "legacy", 42, false, null, and getContext "no" all read as `core`.
    # Stored [], null, and {version: 2} all read as `exposure`.
    cases = (
        {"coreTools": core},
        {"mcpToolExposure": exposure},
        {"coreTools": core, "mcpToolExposure": exposure},
    )
    assert cases
    for config in cases:
        parsed = ScopeDto.model_validate(_scope_with_config(config))
        assert parsed.variation is not None
        row = parsed.variation.interfaces[0].config
        dumped = row.model_dump(by_alias=True, exclude_none=True)
        assert dumped == config
        again = ScopeDto.model_validate(_scope_with_config(dumped))
        assert again.variation is not None
        assert again.variation.interfaces[0].config.model_dump(by_alias=True, exclude_none=True) == dumped

        response = PatchSkillMcpConfigResponseDto.model_validate({"config": config})
        response_dump = response.config.model_dump(by_alias=True, exclude_none=True)
        assert response_dump == config
        resent = PatchSkillMcpConfigResponseDto.model_validate({"config": response_dump})
        assert resent.config.model_dump(by_alias=True, exclude_none=True) == response_dump

    parsed = ScopeDto.model_validate(_scope_with_config({"coreTools": core}))
    assert parsed.variation is not None
    tools = parsed.variation.interfaces[0].config.core_tools
    assert tools is not None
    assert tools.chat is False
    assert tools.get_context is True
    assert tools.teach_modus is False

    for raw in ([], "legacy", 42, False):
        with pytest.raises(ValidationError):
            ScopeDto.model_validate(_scope_with_config({"coreTools": raw}))
        with pytest.raises(ValidationError):
            PatchSkillMcpConfigResponseDto.model_validate({"config": {"coreTools": raw}})
    for raw in ([], {"version": 2}):
        with pytest.raises(ValidationError):
            ScopeDto.model_validate(_scope_with_config({"mcpToolExposure": raw}))
        with pytest.raises(ValidationError):
            PatchSkillMcpConfigResponseDto.model_validate({"config": {"mcpToolExposure": raw}})


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


@pytest.mark.parametrize("reason", ["not_owner", "needs_group_manage"])
def test_workflow_manage_denial_compares_to_wire_string(reason: str) -> None:
    """Permission checks compare the reason to the wire string and read `.value`."""
    from modus.management.resources.workflows.workflows import _parse_workflow

    workflow = _parse_workflow({**_WORKFLOW_DETAIL, "manageDenial": reason})
    denial = workflow.manage_denial
    assert denial is not None
    assert denial == reason
    assert isinstance(denial, str)
    assert denial.value == reason


def test_workflow_manage_denial_null_stays_none() -> None:
    from modus.management.resources.workflows.workflows import _parse_workflow

    workflow = _parse_workflow({**_WORKFLOW_DETAIL, "manageDenial": None})
    assert workflow.manage_denial is None


def test_workflow_dto_flags():
    public = WorkflowDto.model_validate(_WORKFLOW_DETAIL)
    assert public.is_enabled is True
    assert public.has_unpublished_changes is False
