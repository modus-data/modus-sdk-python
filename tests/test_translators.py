"""DTO parsing coverage for SkillDto and AgentDto."""

from modus._generated.models import AgentDto, SkillDto
from modus.types.agents import Agent
from modus.types.skills import Skill

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

_SKILL_BASE = {
    "id": 1,
    "slug": "test-skill",
    "name": "Test Skill",
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

_SKILL_DETAIL = {
    **_SKILL_BASE,
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

_SKILL_LIST = {**_SKILL_BASE, "variation": None}

_AGENT_BASE = {
    "id": 2,
    "slug": "test-agent",
    "name": "Test Agent",
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

_AGENT_DETAIL = {
    **_AGENT_BASE,
    "variation": {"agentSelection": {"agents": [], "model": "gpt-4o-mini"}},
}

_AGENT_LIST = {**_AGENT_BASE, "variation": None}


def test_skill_dto_detail_exposes_variation_instructions():
    public = SkillDto.model_validate(_SKILL_DETAIL)
    assert isinstance(public, Skill)
    assert public.variation is not None
    assert public.variation.instructions == ["Do stuff"]
    assert public.access_config.guardrails == ["no-pii"]


def test_skill_dto_list_row_has_no_variation():
    public = SkillDto.model_validate(_SKILL_LIST)
    assert public.variation is None
    assert public.access_config.guardrails == ["no-pii"]


def test_skill_dto_status_preserved():
    public = SkillDto.model_validate(_SKILL_DETAIL)
    assert public.status == "active"


def test_skill_dto_has_unpublished_changes():
    payload = {**_SKILL_DETAIL, "hasUnpublishedChanges": True}
    assert SkillDto.model_validate(payload).has_unpublished_changes is True


def test_agent_dto_detail_exposes_variation():
    public = AgentDto.model_validate(_AGENT_DETAIL)
    assert isinstance(public, Agent)
    assert public.variation is not None
    assert public.variation.agent_selection is not None


def test_agent_dto_list_row_has_no_variation():
    public = AgentDto.model_validate(_AGENT_LIST)
    assert public.variation is None


def test_agent_dto_type_preserved():
    public = AgentDto.model_validate(_AGENT_DETAIL)
    assert public.type == "task"


def test_agent_dto_flags():
    public = AgentDto.model_validate(_AGENT_DETAIL)
    assert public.is_enabled is True
    assert public.has_unpublished_changes is False
