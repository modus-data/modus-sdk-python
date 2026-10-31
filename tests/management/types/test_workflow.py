"""GET workflow graphs must parse into the editable request model."""

from modus._generated.models import AgentVariationDto
from modus.management.types.workflow import (
    WorkflowGraph,
    dump_workflow_structure,
    parse_workflow_structure,
)

CONDITIONAL_EDGE = {
    "id": "e1",
    "source": "cond",
    "target": "done",
    "sourceHandle": "branch_0",
}


def test_parse_workflow_structure_from_get_response_serializes_request() -> None:
    variation = AgentVariationDto.model_validate(
        {
            "workflowStructure": {"nodes": [], "edges": []},
            "agentSelection": None,
            "trigger": None,
        }
    )
    assert variation.workflow_structure is not None
    graph = parse_workflow_structure(variation.workflow_structure)
    assert graph is not None
    dumped = dump_workflow_structure(graph)
    assert dumped is not None
    assert dumped["nodes"] == []
    assert dumped["edges"] == []


def test_parse_workflow_structure_preserves_conditional_source_handle() -> None:
    variation = AgentVariationDto.model_validate(
        {
            "workflowStructure": {
                "nodes": [
                    {"id": "cond", "type": "condition"},
                    {"id": "done", "type": "action"},
                ],
                "edges": [CONDITIONAL_EDGE],
            },
            "agentSelection": None,
            "trigger": None,
        }
    )
    assert variation.workflow_structure is not None
    graph = parse_workflow_structure(variation.workflow_structure)
    dumped = dump_workflow_structure(graph)
    assert dumped is not None
    edge = dumped["edges"][0]
    assert edge["sourceHandle"] == "branch_0"
    assert "source_handle" not in edge

    again = parse_workflow_structure(graph)
    redumped = dump_workflow_structure(again)
    assert redumped is not None
    assert redumped["edges"][0]["sourceHandle"] == "branch_0"
    assert "source_handle" not in redumped["edges"][0]


def test_parse_workflow_structure_accepts_existing_graph() -> None:
    original = WorkflowGraph(
        nodes=[{"id": "cond", "type": "condition"}],
        edges=[CONDITIONAL_EDGE],
    )
    parsed = parse_workflow_structure(original)
    assert parsed is original
    again = parse_workflow_structure(parsed)
    assert again is original
