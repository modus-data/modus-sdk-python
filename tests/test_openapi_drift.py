"""
L1: OpenAPI drift test.
Verifies that public read types (re-exported DTOs) contain a slot for every field
the backend sends. Subset check: models may have extra fields (forward-compat);
missing fields are bugs. Monorepo-only.
"""
import json
from pathlib import Path

import pytest

_OPENAPI_PATH = Path(__file__).parents[5] / "apps/services/modus-api/openapi/v1.json"

pytestmark = pytest.mark.skipif(
    not _OPENAPI_PATH.exists(),
    reason="openapi/v1.json not found — drift test only runs inside the monorepo",
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


def _model_fields(model_class) -> set:
    return set(model_class.model_fields.keys())


def _camel_to_snake(name: str) -> str:
    import re
    s1 = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", name)
    return re.sub("([a-z0-9])([A-Z])", r"\1_\2", s1).lower()


def _assert_dto_covers_schema(openapi, schema_name: str, model_class) -> None:
    backend = {_camel_to_snake(f) for f in _backend_fields(openapi, schema_name)}
    fields = _model_fields(model_class)
    missing = backend - fields
    assert not missing, (
        f"{model_class.__name__} is missing fields backend sends: {sorted(missing)}.\n"
        f"Regenerate with pnpm nx run modus-sdk-python:generate."
    )


def test_skill_dto_matches_openapi(openapi):
    from modus.types.skills import Skill
    _assert_dto_covers_schema(openapi, "SkillDto", Skill)


def test_agent_dto_matches_openapi(openapi):
    from modus.types.agents import Agent
    _assert_dto_covers_schema(openapi, "AgentDto", Agent)


def test_context_item_matches_openapi(openapi):
    from modus.types.context import ContextItem
    _assert_dto_covers_schema(openapi, "ContextItemDto", ContextItem)


def test_skill_chat_dto_matches_openapi(openapi):
    from modus.types.chat import ChatResult, SkillChatRequestDto

    _assert_dto_covers_schema(openapi, "SkillChatRequestDto", SkillChatRequestDto)
    _assert_dto_covers_schema(openapi, "SkillChatResponseDto", ChatResult)


def test_compose_context_dto_matches_openapi(openapi):
    from modus.types.context_compose import (
        ComposeSkillContextRequest,
        SkillContextComposition,
    )

    _assert_dto_covers_schema(
        openapi, "ComposeSkillContextRequestDto", ComposeSkillContextRequest
    )
    _assert_dto_covers_schema(
        openapi, "ComposeSkillContextResponseDto", SkillContextComposition
    )


def test_automation_run_list_item_matches_openapi(openapi):
    from modus.types.agent_runs import AgentRunListItem
    _assert_dto_covers_schema(openapi, "AutomationRunListItemDto", AgentRunListItem)


def test_usage_bucket_dto_matches_openapi(openapi):
    from modus._generated.models import UsageBucketDto
    _assert_dto_covers_schema(openapi, "UsageBucketDto", UsageBucketDto)


def test_usage_report_matches_openapi(openapi):
    from modus.management.types.usage import UsageReport
    _assert_dto_covers_schema(openapi, "ListUsageResponseDto", UsageReport)
