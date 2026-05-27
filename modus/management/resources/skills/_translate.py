"""Translator: _SkillWire → Skill (management public type).

Key contract: variation fields are flattened onto Skill directly.
On list rows (variation=None), all variation fields are None.
On .get() rows (variation present), fields are populated from the dict.
guardrails is always read from accessConfig (default []).
"""
from __future__ import annotations

from ...types.access import AccessConfig
from ...types.skills import Skill
from ..._wire.skills import _SkillWire


def _translate_skill(wire: _SkillWire) -> Skill:
    variation: dict = wire.variation or {}
    access_raw: dict = wire.access_config or {}

    return Skill(
        # Identity
        id=wire.id,
        slug=wire.slug,
        name=wire.name,
        status=wire.status,  # type: ignore[arg-type]
        description=wire.description,
        org_uuid=wire.org_uuid,
        # Version state
        has_unpublished_changes=wire.has_unpublished_changes,
        active_variation_id=wire.active_variation_id,
        draft_variation_id=wire.draft_variation_id,
        # Variation fields — None when variation absent (list rows)
        instructions=variation.get("instructions"),
        model=variation.get("model"),
        expected_output=variation.get("expectedOutput"),
        toolset=variation.get("toolset"),
        connection_set=variation.get("connectionSet"),
        context_selections=variation.get("contextSelections"),
        interfaces=variation.get("interfaces"),
        evaluations=variation.get("evaluations"),
        # Guardrails + access config from accessConfig
        guardrails=access_raw.get("guardrails", []),
        access_config=AccessConfig(
            guardrails=access_raw.get("guardrails", []),
            permissions=access_raw.get("permissions", {}),
        ),
        # Timestamps
        created_at=wire.created_at,
        updated_at=wire.updated_at,
        deleted_at=wire.deleted_at,
    )
