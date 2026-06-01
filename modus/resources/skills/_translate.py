"""Translator: _SkillWire → Skill (consumption public type)."""
from ...types.skills import Skill
from ..._wire.skills import _SkillWire


def _translate_skill(wire: _SkillWire) -> Skill:
    """Map the full wire model to the identity-only consumption Skill."""
    return Skill(
        id=wire.id,
        slug=wire.slug,
        name=wire.name,
        status=wire.status,  # type: ignore[arg-type]
        description=wire.description,
        has_unpublished_changes=wire.has_unpublished_changes,
    )
