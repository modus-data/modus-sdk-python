"""Verify consumption Skill/Agent shape — read-only config subset."""
from modus.types.agents import Agent
from modus.types.skills import Skill


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


def test_skill_exposes_instructions_and_guardrails():
    assert "instructions" in Skill.model_fields
    assert "guardrails" in Skill.model_fields


def test_agent_exposes_instructions_and_guardrails():
    assert "instructions" in Agent.model_fields
    assert "guardrails" in Agent.model_fields


def test_skill_identity_fields_present():
    s = Skill(id=1, slug="s", name="N", status="active", description=None)
    assert s.id == 1
    assert s.slug == "s"
    assert s.status == "active"
    assert s.description is None
    assert s.guardrails == []


def test_agent_identity_fields_present():
    a = Agent(id=7, slug="r", name="Report", status="active", type="task", description=None)
    assert a.id == 7
    assert a.type == "task"
