"""Translator: _SkillWire → Skill (management public type).

Key contract: variation fields are flattened onto Skill directly.
On list rows (variation=None), all variation fields are None.
On .get() rows (variation present), fields are populated from the dict.
guardrails is always read from accessConfig (default []).
"""
from __future__ import annotations

from ..._wire.skills import _SkillWire
from ...types.access import AccessConfig
from ...types.json_blob import parse_json_object_list
from ...types.skills import Skill
from ...types.toolset import parse_toolset


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
        toolset=parse_toolset(variation.get("toolset")),
        connection_set=parse_json_object_list(
            variation.get("connectionSet") or variation.get("connection_set")
        ),
        context_selections=parse_json_object_list(
            variation.get("contextSelections") or variation.get("context_selections")
        ),
        interfaces=parse_json_object_list(
            variation.get("interfaces")
        ),
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
