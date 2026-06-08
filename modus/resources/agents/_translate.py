"""Translator: _AgentWire → Agent (consumption public type)."""
from __future__ import annotations

from typing import List, Optional

from ..._wire.agents import _AgentWire
from ...types.agents import Agent


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


def _translate_agent(wire: _AgentWire) -> Agent:
    """Map wire to consumption Agent (identity + read-only instructions/guardrails)."""
    return Agent(
        id=wire.id,
        slug=wire.slug,
        name=wire.name,
        status=wire.status,  # type: ignore[arg-type]
        type=wire.type,  # type: ignore[arg-type]
        description=wire.description,
        has_unpublished_changes=wire.has_unpublished_changes,
        is_enabled=wire.is_enabled,
        instructions=_instructions_from_variation(wire.variation),
        guardrails=_guardrails_from_access(wire.access_config),
    )
