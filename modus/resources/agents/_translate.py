"""Translator: _AgentWire → Agent (consumption public type)."""
from ...types.agents import Agent
from ..._wire.agents import _AgentWire


def _translate_agent(wire: _AgentWire) -> Agent:
    """Map the full wire model to the identity-only consumption Agent."""
    return Agent(
        id=wire.id,
        slug=wire.slug,
        name=wire.name,
        status=wire.status,  # type: ignore[arg-type]
        type=wire.type,  # type: ignore[arg-type]
        description=wire.description,
        has_unpublished_changes=wire.has_unpublished_changes,
        is_enabled=wire.is_enabled,
    )
