"""Verify consumption Skill/Agent expose the full OpenAPI read shape (DTO re-exports)."""

from modus.types.agents import Agent
from modus.types.skills import Skill


def test_skill_exposes_variation_and_access_config_fields():
    assert "variation" in Skill.model_fields
    assert "access_config" in Skill.model_fields
    assert "org_uuid" in Skill.model_fields


def test_agent_exposes_variation_and_access_config_fields():
    assert "variation" in Agent.model_fields
    assert "access_config" in Agent.model_fields


def test_skill_variation_nested_config():
    skill = Skill.model_validate(
        {
            "id": 1,
            "slug": "s",
            "name": "N",
            "status": "active",
            "description": None,
            "orgUuid": "org-1",
            "hasUnpublishedChanges": False,
            "activeVariationId": None,
            "draftVariationId": None,
            "accessConfig": {
                "visibility": "shared",
                "groupPermissions": {"__everyone__": {"use": True, "manage": True}},
                "guardrails": ["no-pii"],
                "sharedWith": [],
            },
            "createdAt": "2026-01-01T00:00:00Z",
            "updatedAt": "2026-01-01T00:00:00Z",
            "deletedAt": None,
            "canManage": True,
            "canUse": True,
            "manageDenial": None,
            "variation": {
                "instructions": ["Do stuff"],
                "model": "gpt-4o",
                "expectedOutput": "out",
                "toolset": {},
                "connectionSet": [],
                "contextSelections": [],
                "interfaces": [],
                "evaluations": [],
                "supervisionSubordinateIds": [],
                "supervisionSubordinateDescriptions": {},
            },
        }
    )
    assert skill.variation is not None
    assert skill.variation.instructions == ["Do stuff"]
    assert skill.access_config.guardrails == ["no-pii"]


def test_skill_identity_fields_present():
    skill = Skill.model_validate(
        {
            "id": 1,
            "slug": "s",
            "name": "N",
            "status": "active",
            "description": None,
            "orgUuid": "org-1",
            "hasUnpublishedChanges": False,
            "activeVariationId": None,
            "draftVariationId": None,
            "accessConfig": {
                "visibility": "shared",
                "groupPermissions": {"__everyone__": {"use": True, "manage": True}},
                "guardrails": [],
                "sharedWith": [],
            },
            "createdAt": "2026-01-01T00:00:00Z",
            "updatedAt": "2026-01-01T00:00:00Z",
            "deletedAt": None,
            "canManage": True,
            "canUse": True,
            "manageDenial": None,
        }
    )
    assert skill.id == 1
    assert skill.slug == "s"
    assert skill.status == "active"
    assert skill.description is None


def test_agent_identity_fields_present():
    agent = Agent.model_validate(
        {
            "id": 7,
            "slug": "r",
            "name": "Report",
            "status": "active",
            "type": "task",
            "description": None,
            "orgUuid": "org-1",
            "hasUnpublishedChanges": False,
            "isEnabled": True,
            "activeVariationId": None,
            "draftVariationId": None,
            "accessConfig": {
                "visibility": "shared",
                "groupPermissions": {"__everyone__": {"use": True, "manage": True}},
                "sharedWith": [],
            },
            "createdAt": "2026-01-01T00:00:00Z",
            "updatedAt": "2026-01-01T00:00:00Z",
            "deletedAt": None,
            "canManage": True,
            "canUse": True,
            "manageDenial": None,
        }
    )
    assert agent.id == 7
    assert agent.type == "task"
