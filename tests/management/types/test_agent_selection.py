"""Tests for AgentSelection typed models and serialization."""

import pytest
from modus.management.types.agent_selection import (
    AgentSelection,
    AgentSelectionEntry,
    dump_agent_selection,
    parse_agent_selection,
)
from pydantic import ValidationError


def test_single_factory() -> None:
    selection = AgentSelection.single(17, model="gpt-4o")
    assert len(selection.agents) == 1
    assert selection.agents[0].agent_id == 17
    assert selection.agents[0].priority_order == 1
    assert selection.model == "gpt-4o"


def test_ordered_factory() -> None:
    selection = AgentSelection.ordered(
        [
            AgentSelectionEntry(agent_id=1, priority_order=1, role="researcher"),
            AgentSelectionEntry(agent_id=2, priority_order=2),
        ],
        model="claude-sonnet-5",
    )
    assert len(selection.agents) == 2
    assert selection.agents[0].role == "researcher"


def test_entry_rejects_invalid_agent_id() -> None:
    with pytest.raises(ValidationError):
        AgentSelectionEntry(agent_id=0, priority_order=1)


def test_dump_agent_selection_snake_case() -> None:
    payload = dump_agent_selection(AgentSelection.single(17, model="gpt-4o"))
    assert payload == {
        "agents": [{"agent_id": 17, "priority_order": 1}],
        "model": "gpt-4o",
    }
    entry = payload["agents"][0]
    assert "agent_id" in entry
    assert "priority_order" in entry
    assert "agentId" not in entry
    assert "priorityOrder" not in entry


def test_dump_agent_selection_rejects_raw_dict() -> None:
    with pytest.raises(TypeError, match="AgentSelection"):
        dump_agent_selection({"agents": [{"agent_id": 1, "priority_order": 1}]})


def test_parse_agent_selection_accepts_camel_case_inbound() -> None:
    raw = {
        "agents": [{"agentId": 17, "priorityOrder": 1, "role": "analyst"}],
        "model": "gpt-4o",
    }
    selection = parse_agent_selection(raw)
    assert selection is not None
    assert selection.agents[0].agent_id == 17
    assert selection.agents[0].role == "analyst"


def test_parse_agent_selection_from_get_response_serializes_request() -> None:
    from modus._generated.models import AgentVariationDto

    variation = AgentVariationDto.model_validate(
        {
            "agentSelection": {"agents": [{"agent_id": 10, "priority_order": 1}]},
            "workflowStructure": {"nodes": [], "edges": []},
            "trigger": None,
        }
    )
    assert variation.agent_selection is not None
    assert len(variation.agent_selection.agents) == 1
    selection = parse_agent_selection(variation.agent_selection)
    assert selection is not None
    dumped = dump_agent_selection(selection)
    assert dumped is not None
    assert dumped["agents"]
    assert dumped == {"agents": [{"agent_id": 10, "priority_order": 1}]}
    assert "agentId" not in dumped["agents"][0]


def test_parse_agent_selection_keeps_model_settings_for_update() -> None:
    """A GET selection sent back on update keeps its modelSettings, which the API would otherwise clear."""
    from modus._generated.models import AgentVariationDto

    variation = AgentVariationDto.model_validate(
        {
            "agentSelection": {
                "agents": [{"agent_id": 10, "priority_order": 1}],
                "model": "gpt-4o",
                "modelSettings": {"reasoningEffort": "low", "contextWindow": 128000},
            },
            "workflowStructure": None,
            "trigger": None,
        }
    )
    assert variation.agent_selection is not None
    assert variation.agent_selection.model_settings is not None
    selection = parse_agent_selection(variation.agent_selection)
    assert selection is not None
    assert selection.model == "gpt-4o"
    assert selection.agents[0].agent_id == 10
    dumped = dump_agent_selection(selection)
    assert dumped == {
        "agents": [{"agent_id": 10, "priority_order": 1}],
        "model": "gpt-4o",
        "modelSettings": {"reasoningEffort": "low", "contextWindow": 128000},
    }


def test_parse_agent_selection_accepts_existing_model() -> None:
    original = AgentSelection.single(10)
    parsed = parse_agent_selection(original)
    assert parsed is original
    again = parse_agent_selection(parsed)
    assert again is original
    dumped = dump_agent_selection(again)
    assert dumped == {"agents": [{"agent_id": 10, "priority_order": 1}]}


def test_parse_dump_round_trip() -> None:
    raw = {
        "agents": [{"agentId": 42, "priorityOrder": 1}],
        "model": "gpt-4o-mini",
    }
    selection = parse_agent_selection(raw)
    assert selection is not None
    dumped = dump_agent_selection(selection)
    assert dumped == {
        "agents": [{"agent_id": 42, "priority_order": 1}],
        "model": "gpt-4o-mini",
    }
