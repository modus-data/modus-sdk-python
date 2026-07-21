"""Test DTO parsing for management SDK scope/workflow payloads."""

from modus._generated.models import ScopeDto, WorkflowDto
from modus.management.types.agents import Agent
from modus.management.types.skills import Skill

PENDING_OWNERSHIP_TRANSFER = {
    "pendingOwnerUserId": "user_pending",
    "pendingOwnerEmail": "newowner@example.com",
    "requestedByUserId": "user_owner",
    "requestedAt": "2026-06-05T12:00:00.000Z",
}


def test_scope_dto_parses_list_row(skill_list_row):
    skill = ScopeDto.model_validate(skill_list_row)
    assert skill.id == 10
    assert skill.variation is None


def test_scope_dto_parses_detail_row(skill_detail_row):
    skill = ScopeDto.model_validate(skill_detail_row)
    assert skill.variation is not None
    assert skill.variation.instructions == [
        "You are a Snowflake data analyst.",
        "Use SQL for queries.",
    ]


def test_scope_dto_parses_guardrails_from_access_config(skill_list_row):
    skill = ScopeDto.model_validate(skill_list_row)
    assert skill.access_config.guardrails == ["no-pii"]


def test_workflow_dto_parses_list_row(agent_list_row):
    agent = WorkflowDto.model_validate(agent_list_row)
    assert agent.id == 5
    assert agent.type == "task"
    assert agent.variation is None


def test_scope_dto_list_row_has_none_variation(skill_list_row):
    skill = ScopeDto.model_validate(skill_list_row)
    assert isinstance(skill, Skill)
    assert skill.variation is None


def test_scope_dto_list_row_has_guardrails(skill_list_row):
    skill = ScopeDto.model_validate(skill_list_row)
    assert skill.access_config.guardrails == ["no-pii"]


def test_scope_dto_detail_row_exposes_variation_fields(skill_detail_row):
    skill = ScopeDto.model_validate(skill_detail_row)
    assert skill.variation is not None
    assert skill.variation.model == "gpt-4o"
    assert skill.variation.expected_output == "Structured JSON with data rows"
    assert skill.variation.toolset is not None
    assert skill.variation.connection_set is not None
    assert skill.variation.connection_set[0]["connectionId"] == "conn-snowflake-001"


def test_scope_dto_maps_pending_ownership_transfer(skill_detail_row):
    skill = ScopeDto.model_validate(
        {
            **skill_detail_row,
            "pendingOwnershipTransfer": PENDING_OWNERSHIP_TRANSFER,
        }
    )
    assert skill.pending_ownership_transfer is not None
    assert skill.pending_ownership_transfer.pending_owner_user_id == "user_pending"
    assert skill.pending_ownership_transfer.pending_owner_email == "newowner@example.com"
    assert skill.pending_ownership_transfer.requested_by_user_id == "user_owner"


def test_workflow_dto_maps_pending_ownership_transfer(agent_list_row):
    agent = WorkflowDto.model_validate(
        {
            **agent_list_row,
            "pendingOwnershipTransfer": PENDING_OWNERSHIP_TRANSFER,
        }
    )
    assert agent.pending_ownership_transfer is not None
    assert agent.pending_ownership_transfer.pending_owner_user_id == "user_pending"


def test_workflow_dto_detail_row_exposes_variation_fields(agent_detail_row):
    agent = WorkflowDto.model_validate(agent_detail_row)
    assert isinstance(agent, Agent)
    assert agent.variation is not None
    assert agent.variation.agent_selection is not None
    assert agent.variation.agent_selection["model"] == "gpt-4o-mini"
