"""Translator: _SkillWire → Skill (consumption public type)."""
from __future__ import annotations

from typing import List, Optional

from ..._wire.skills import _SkillWire
from ...types.skills import Skill


def _instructions_from_variation(variation: Optional[dict]) -> Optional[List[str]]:
    if not variation:
        return None
    raw = variation.get("instructions")
    return raw if isinstance(raw, list) else None


def _guardrails_from_access(access_config: Optional[dict]) -> List[str]:
    if not access_config:
        return []
    raw = access_config.get("guardrails")
    return raw if isinstance(raw, list) else []


def _translate_skill(wire: _SkillWire) -> Skill:
    """Map wire to consumption Skill (identity + read-only instructions/guardrails)."""
    return Skill(
        id=wire.id,
        slug=wire.slug,
        name=wire.name,
        status=wire.status,  # type: ignore[arg-type]
        description=wire.description,
        has_unpublished_changes=wire.has_unpublished_changes,
        instructions=_instructions_from_variation(wire.variation),
        guardrails=_guardrails_from_access(wire.access_config),
    )
