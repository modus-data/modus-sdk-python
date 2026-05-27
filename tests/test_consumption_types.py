"""Verify consumption Skill/Agent expose only identity fields."""
import pytest
from modus.types.skills import Skill
from modus.types.agents import Agent


def test_skill_has_no_variation_field():
    """Consumption Skill must not expose variation — that's management only."""
    assert "variation" not in Skill.model_fields, \
        "Skill.variation must not exist in consumption SDK"


def test_skill_has_no_org_uuid():
    assert "org_uuid" not in Skill.model_fields, \
        "Skill.org_uuid must not exist in consumption SDK"


def test_agent_has_no_variation_field():
    assert "variation" not in Agent.model_fields, \
        "Agent.variation must not exist in consumption SDK"


def test_skill_identity_fields_present():
    s = Skill(id=1, slug="s", name="N", status="active", description=None)
    assert s.id == 1
    assert s.slug == "s"
    assert s.status == "active"
    assert s.description is None


def test_agent_identity_fields_present():
    a = Agent(id=7, slug="r", name="Report", status="active", type="task", description=None)
    assert a.id == 7
    assert a.type == "task"
