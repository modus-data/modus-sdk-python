"""Translator: _AgentWire → Agent (management public type).

variation fields are flattened: instructions, model.
guardrails always read from accessConfig.
"""
from __future__ import annotations

from ..._wire.agents import _AgentWire
from ...types.access import AccessConfig
from ...types.agent_selection import parse_agent_selection
from ...types.agents import Agent
from ...types.ownership import parse_pending_ownership_transfer
from ...types.triggers import parse_trigger
from ...types.workflow import parse_workflow_structure


def _translate_agent(wire: _AgentWire) -> Agent:
    variation: dict = wire.variation or {}
    access_raw: dict = wire.access_config or {}

    return Agent(
        id=wire.id,
        slug=wire.slug,
        name=wire.name,
        status=wire.status,  # type: ignore[arg-type]
        type=wire.type,  # type: ignore[arg-type]
        description=wire.description,
        org_uuid=wire.org_uuid,
        has_unpublished_changes=wire.has_unpublished_changes,
        is_enabled=wire.is_enabled,
        active_variation_id=wire.active_variation_id,
        draft_variation_id=wire.draft_variation_id,
        # Variation fields
        instructions=variation.get("instructions"),
        model=variation.get("model"),
        trigger=parse_trigger(variation.get("trigger")),
        agent_selection=parse_agent_selection(variation.get("agentSelection") or variation.get("agent_selection")),
        workflow_structure=parse_workflow_structure(
            variation.get("workflowStructure") or variation.get("workflow_structure")
        ),
        # Access config
        guardrails=access_raw.get("guardrails", []),
        access_config=AccessConfig(
            guardrails=access_raw.get("guardrails", []),
            permissions=access_raw.get("permissions", {}),
        ),
        pending_ownership_transfer=parse_pending_ownership_transfer(
            wire.pending_ownership_transfer
        ),
        created_at=wire.created_at,
        updated_at=wire.updated_at,
        deleted_at=wire.deleted_at,
    )
