"""
L2: Translator coverage test.
Verifies that every field on the public Skill/Agent type is populated
by the translator. Catches: new public field added but translator forgot
to wire it up.
"""
from datetime import datetime, timezone

from modus._wire.agents import _AgentWire
from modus._wire.skills import _SkillWire
from modus.resources.agents._translate import _translate_agent
from modus.resources.skills._translate import _translate_skill
from modus.types.agents import Agent
from modus.types.skills import Skill

_NOW = datetime(2026, 1, 1, tzinfo=timezone.utc)

WIRE_SKILL = _SkillWire(
    id=1, slug="test-skill", name="Test Skill", status="active",
    org_uuid="org-uuid", has_unpublished_changes=False,
    active_variation_id="var-1", draft_variation_id=None,
    access_config=None,
    created_at=_NOW, updated_at=_NOW, deleted_at=None,
    variation={"instructions": ["Do stuff"]},
)

WIRE_AGENT = _AgentWire(
    id=2, slug="test-agent", name="Test Agent", status="active",
    type="task", org_uuid="org-uuid", has_unpublished_changes=False,
    active_variation_id="var-2", draft_variation_id=None,
    is_enabled=True, access_config=None,
    created_at=_NOW, updated_at=_NOW, deleted_at=None,
    variation=None,
)


def test_translate_skill_populates_all_public_fields():
    public = _translate_skill(WIRE_SKILL)
    assert isinstance(public, Skill)
    public_fields = set(Skill.model_fields.keys())
    wire_fields = set(_SkillWire.model_fields.keys())
    # Every public field must be derivable from wire fields (properties excluded)
    unmapped = public_fields - wire_fields - {"is_active", "is_draft"}
    assert not unmapped, f"Public Skill has fields not mapped by translator: {unmapped}"


def test_translate_skill_variation_not_exposed():
    """Consumption Skill must not expose variation — both at the schema level
    and on the translated payload."""
    public = _translate_skill(WIRE_SKILL)
    # Schema-level: the type doesn't declare a `variation` field.
    assert "variation" not in Skill.model_fields
    # Translator-level: the dumped instance doesn't expose it either.
    # (catches a regression where the translator might leak the wire dict).
    assert "variation" not in public.model_dump()


def test_translate_skill_status_preserved():
    public = _translate_skill(WIRE_SKILL)
    assert public.status == "active"
    assert public.is_active is True
    assert public.is_draft is False


def test_translate_skill_has_unpublished_changes():
    wire = WIRE_SKILL.model_copy(update={"has_unpublished_changes": True})
    assert _translate_skill(wire).has_unpublished_changes is True


def test_translate_agent_populates_all_public_fields():
    public = _translate_agent(WIRE_AGENT)
    assert isinstance(public, Agent)
    public_fields = set(Agent.model_fields.keys())
    wire_fields = set(_AgentWire.model_fields.keys())
    unmapped = public_fields - wire_fields - {"is_active", "is_draft"}
    assert not unmapped, f"Public Agent has fields not mapped by translator: {unmapped}"


def test_translate_agent_type_preserved():
    public = _translate_agent(WIRE_AGENT)
    assert public.type == "task"


def test_translate_agent_flags():
    public = _translate_agent(WIRE_AGENT)
    assert public.is_enabled is True
    assert public.has_unpublished_changes is False
