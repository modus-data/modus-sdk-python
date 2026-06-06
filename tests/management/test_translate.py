"""Test wire model parsing for management SDK."""

from modus.management._wire.agents import _AgentWire
from modus.management._wire.skills import _SkillWire

SKILL_LIST_WIRE = {
    "id": 10, "slug": "snowflake-analyst", "name": "Snowflake Analyst",
    "status": "active", "description": "Desc", "orgUuid": "org-xyz",
    "hasUnpublishedChanges": False, "activeVariationId": "var-001",
    "draftVariationId": None,
    "accessConfig": {"guardrails": ["no-pii"], "permissions": {}},
    "createdAt": "2026-01-01T00:00:00.000Z",
    "updatedAt": "2026-03-01T00:00:00.000Z",
    "deletedAt": None,
    # NO variation key — simulates a list-endpoint row
}

SKILL_DETAIL_WIRE = {
    **SKILL_LIST_WIRE,
    "variation": {
        "instructions": ["You are a Snowflake analyst.", "Use SQL."],
        "model": "gpt-4o",
        "expectedOutput": "JSON rows",
        "toolset": {"sql": {"enabled": True}},
        "connectionSet": [{"connectionId": "conn-001"}],
        "contextSelections": [],
        "interfaces": [],
        "evaluations": [],
    },
}


def test_skill_wire_parses_list_row():
    wire = _SkillWire.model_validate(SKILL_LIST_WIRE)
    assert wire.id == 10
    assert wire.variation is None  # absent in list rows


def test_skill_wire_parses_detail_row():
    wire = _SkillWire.model_validate(SKILL_DETAIL_WIRE)
    assert wire.variation is not None
    assert wire.variation["instructions"] == ["You are a Snowflake analyst.", "Use SQL."]


def test_skill_wire_parses_guardrails_from_access_config():
    wire = _SkillWire.model_validate(SKILL_LIST_WIRE)
    assert wire.access_config == {"guardrails": ["no-pii"], "permissions": {}}


def test_agent_wire_parses_list_row():
    wire = _AgentWire.model_validate({
        "id": 5, "slug": "weekly-report", "name": "Weekly Revenue Report",
        "status": "active", "type": "task", "description": "Reports",
        "orgUuid": "org-xyz", "hasUnpublishedChanges": False,
        "isEnabled": True, "activeVariationId": "avar-001", "draftVariationId": None,
        "accessConfig": {"guardrails": [], "permissions": {}},
        "createdAt": "2026-01-01T00:00:00.000Z",
        "updatedAt": "2026-02-01T00:00:00.000Z",
        "deletedAt": None,
    })
    assert wire.id == 5
    assert wire.type == "task"
    assert wire.variation is None


# --- Public type translators (Task 7) -----------------------------------------

from modus.management.resources.agents._translate import _translate_agent
from modus.management.resources.skills._translate import _translate_skill
from modus.management.types.agents import Agent
from modus.management.types.skills import Skill


def test_translate_skill_list_row_has_none_variation_fields():
    """List rows must have instructions=None, model=None (variation absent)."""
    wire = _SkillWire.model_validate(SKILL_LIST_WIRE)
    skill = _translate_skill(wire)
    assert isinstance(skill, Skill)
    assert skill.instructions is None
    assert skill.model is None
    assert skill.expected_output is None
    assert skill.toolset is None


def test_translate_skill_list_row_has_guardrails():
    """guardrails must be surfaced from accessConfig even on list rows."""
    wire = _SkillWire.model_validate(SKILL_LIST_WIRE)
    skill = _translate_skill(wire)
    assert skill.guardrails == ["no-pii"]


def test_translate_skill_detail_row_flattens_variation():
    """get() rows must expose variation fields at the top level."""
    wire = _SkillWire.model_validate(SKILL_DETAIL_WIRE)
    skill = _translate_skill(wire)
    assert skill.instructions == ["You are a Snowflake analyst.", "Use SQL."]
    assert skill.model == "gpt-4o"
    assert skill.expected_output == "JSON rows"
    assert skill.toolset is not None
    assert skill.toolset.model_dump().get("sql") == {"enabled": True}
    assert skill.connection_set is not None
    assert skill.connection_set[0].model_dump(by_alias=True).get("connectionId") == "conn-001"


def test_translate_skill_has_no_variation_attribute():
    """The public Skill type must not expose raw variation dict."""
    wire = _SkillWire.model_validate(SKILL_DETAIL_WIRE)
    skill = _translate_skill(wire)
    assert not hasattr(skill, "variation"), "Skill must not expose raw variation"


def test_translate_agent_list_row_has_none_variation_fields():
    wire = _AgentWire.model_validate({
        "id": 5, "slug": "r", "name": "Report", "status": "active",
        "type": "task", "orgUuid": "org-xyz", "hasUnpublishedChanges": False,
        "isEnabled": True, "accessConfig": {"guardrails": [], "permissions": {}},
        "createdAt": "2026-01-01T00:00:00.000Z",
        "updatedAt": "2026-01-01T00:00:00.000Z", "deletedAt": None,
    })
    agent = _translate_agent(wire)
    assert isinstance(agent, Agent)
    assert agent.instructions is None
    assert agent.model is None


PENDING_OWNERSHIP_TRANSFER = {
    "pendingOwnerUserId": "user_pending",
    "pendingOwnerEmail": "newowner@example.com",
    "requestedByUserId": "user_owner",
    "requestedAt": "2026-06-05T12:00:00.000Z",
}


def test_translate_skill_maps_pending_ownership_transfer():
    wire = _SkillWire.model_validate({
        **SKILL_DETAIL_WIRE,
        "pendingOwnershipTransfer": PENDING_OWNERSHIP_TRANSFER,
    })
    skill = _translate_skill(wire)
    assert skill.pending_ownership_transfer is not None
    assert skill.pending_ownership_transfer.pending_owner_user_id == "user_pending"
    assert skill.pending_ownership_transfer.pending_owner_email == "newowner@example.com"
    assert skill.pending_ownership_transfer.requested_by_user_id == "user_owner"


def test_translate_agent_maps_pending_ownership_transfer():
    wire = _AgentWire.model_validate({
        "id": 5, "slug": "r", "name": "Report", "status": "active",
        "type": "task", "orgUuid": "org-xyz", "hasUnpublishedChanges": False,
        "isEnabled": True, "accessConfig": {"guardrails": [], "permissions": {}},
        "createdAt": "2026-01-01T00:00:00.000Z",
        "updatedAt": "2026-01-01T00:00:00.000Z", "deletedAt": None,
        "pendingOwnershipTransfer": PENDING_OWNERSHIP_TRANSFER,
    })
    agent = _translate_agent(wire)
    assert agent.pending_ownership_transfer is not None
    assert agent.pending_ownership_transfer.pending_owner_user_id == "user_pending"


def test_translate_agent_detail_row_flattens_variation():
    wire = _AgentWire.model_validate({
        "id": 5, "slug": "r", "name": "Report", "status": "active",
        "type": "task", "orgUuid": "org-xyz", "hasUnpublishedChanges": False,
        "isEnabled": True, "accessConfig": {"guardrails": [], "permissions": {}},
        "createdAt": "2026-01-01T00:00:00.000Z",
        "updatedAt": "2026-01-01T00:00:00.000Z", "deletedAt": None,
        "variation": {"instructions": ["Run the SQL and email results."], "model": "gpt-4o-mini"},
    })
    agent = _translate_agent(wire)
    assert agent.instructions == ["Run the SQL and email results."]
    assert agent.model == "gpt-4o-mini"
