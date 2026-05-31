"""
L1: OpenAPI drift test.
Verifies that wire models contain a slot for every field the backend sends.
Subset check: wire may have extra fields (forward-compat); missing fields are bugs.
This test is monorepo-only — skipped gracefully outside the monorepo.
"""
import json
import pytest
from pathlib import Path

# Locate openapi spec relative to monorepo root. The SDK lives at
# `sdk/python/consumption/tests/` — four parents up reaches the repo root.
_OPENAPI_PATH = Path(__file__).parents[4] / "apps/services/modus-api/openapi/v1.json"

pytestmark = pytest.mark.skipif(
    not _OPENAPI_PATH.exists(),
    reason="openapi/v1.json not found — drift test only runs inside the monorepo"
)


@pytest.fixture(scope="module")
def openapi():
    return json.loads(_OPENAPI_PATH.read_text())


def _backend_fields(openapi, schema_name: str) -> set:
    schemas = openapi.get("components", {}).get("schemas", {})
    if schema_name not in schemas:
        raise KeyError(
            f"Schema '{schema_name}' not found in OpenAPI spec. "
            f"Available schemas: {sorted(schemas.keys())}"
        )
    schema = schemas[schema_name]
    if "properties" not in schema:
        raise KeyError(
            f"Schema '{schema_name}' has no 'properties' key — cannot detect drift."
        )
    return set(schema["properties"].keys())


def _wire_fields(model_class) -> set:
    return set(model_class.model_fields.keys())


def _camel_to_snake(name: str) -> str:
    import re
    s1 = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", name)
    return re.sub("([a-z0-9])([A-Z])", r"\1_\2", s1).lower()


def test_skill_wire_matches_openapi(openapi):
    from modus._wire.skills import _SkillWire
    backend = {_camel_to_snake(f) for f in _backend_fields(openapi, "SkillDto")}
    wire = _wire_fields(_SkillWire)
    missing = backend - wire
    assert not missing, (
        f"_SkillWire is missing fields backend sends: {sorted(missing)}.\n"
        f"Update modus/_wire/skills.py and add to _translate_skill() in resources/skills/_translate.py"
    )


def test_agent_wire_matches_openapi(openapi):
    from modus._wire.agents import _AgentWire
    backend = {_camel_to_snake(f) for f in _backend_fields(openapi, "AgentDto")}
    wire = _wire_fields(_AgentWire)
    missing = backend - wire
    assert not missing, (
        f"_AgentWire is missing fields backend sends: {sorted(missing)}.\n"
        f"Update modus/_wire/agents.py and add to _translate_agent() in resources/agents/_translate.py"
    )


def test_context_item_matches_openapi(openapi):
    from modus.types.context import ContextItem
    backend = {_camel_to_snake(f) for f in _backend_fields(openapi, "ContextItemDto")}
    public = _wire_fields(ContextItem)
    missing = backend - public
    assert not missing, (
        f"ContextItem is missing fields backend sends: {sorted(missing)}.\n"
        f"Update modus/types/context.py"
    )


def test_skill_chat_wire_matches_openapi(openapi):
    from modus._wire.chat import _SkillChatRequestWire, _SkillChatResponseWire

    req_backend = {_camel_to_snake(f) for f in _backend_fields(openapi, "SkillChatRequestDto")}
    assert not (req_backend - _wire_fields(_SkillChatRequestWire))

    resp_backend = {_camel_to_snake(f) for f in _backend_fields(openapi, "SkillChatResponseDto")}
    assert not (resp_backend - _wire_fields(_SkillChatResponseWire))


def test_compose_context_wire_matches_openapi(openapi):
    from modus._wire.context_compose import (
        _ComposeSkillContextRequestWire,
        _ComposeSkillContextResponseWire,
    )

    req_backend = {
        _camel_to_snake(f) for f in _backend_fields(openapi, "ComposeSkillContextRequestDto")
    }
    assert not (req_backend - _wire_fields(_ComposeSkillContextRequestWire))

    resp_backend = {
        _camel_to_snake(f) for f in _backend_fields(openapi, "ComposeSkillContextResponseDto")
    }
    assert not (resp_backend - _wire_fields(_ComposeSkillContextResponseWire))


def test_automation_run_list_item_wire_matches_openapi(openapi):
    from modus._wire.agent_runs import _AutomationRunListItemWire

    backend = {
        _camel_to_snake(f) for f in _backend_fields(openapi, "AutomationRunListItemDto")
    }
    wire = _wire_fields(_AutomationRunListItemWire)
    missing = backend - wire
    assert not missing, (
        f"_AutomationRunListItemWire missing backend fields: {sorted(missing)}"
    )
