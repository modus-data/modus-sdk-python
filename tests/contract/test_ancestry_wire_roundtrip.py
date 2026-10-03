"""Ancestry is optional on context items; wire names stay snake_case on entries."""

from __future__ import annotations

from modus._generated.models import (
    AgentSelectionEntryDto,
    Frequency,
    MemberGroupDto,
    OrgMemberDto,
    TriggerDto,
    TriggerScheduleDto,
    TriggerType,
    UsageTotalsDto,
)
from modus.types.context import ContextItem, ContextItemLookupRow

REQUIRED_ITEM = {
    "uid": "7a3f9d2c-1111-4000-a000-000000000abc",
    "orgId": "org-uuid-abc",
    "contextType": "note",
    "description": None,
    "content": {"title": "Q3 notes"},
    "userFeedback": "neutral",
    "topics": [],
    "connectionId": None,
    "selectionId": None,
    "dataPath": ["custom", "note-1"],
    "createdAt": "2026-01-01T00:00:00.000Z",
    "updatedAt": "2026-01-01T00:00:00.000Z",
}

RICH_ANCESTRY = [
    {"uid": "seg-a", "display_name": "A", "type": "container"},
    {"uid": "seg-b", "display_name": "B", "type": None},
]

LOOKUP_REQUIRED = {
    "uid": "note-1",
    "contextType": "note",
    "content": {"title": "Q3 notes"},
    "connectionId": None,
    "selectionId": None,
    "dataPath": ["custom", "note-1"],
}


def test_context_item_omitted_ancestry_is_optional() -> None:
    item = ContextItem.model_validate(REQUIRED_ITEM)
    assert "ancestry" not in item.model_fields_set
    assert item.ancestry is None
    assert "ancestry" not in item.model_dump(by_alias=True, exclude_unset=True)
    assert ContextItem.model_fields["ancestry"].is_required() is False


def test_context_item_null_ancestry_round_trips() -> None:
    item = ContextItem.model_validate({**REQUIRED_ITEM, "ancestry": None})
    dumped = item.model_dump(by_alias=True)
    assert dumped["ancestry"] is None
    assert "ancestry" in item.model_dump(by_alias=True, exclude_unset=True)
    reparsed = ContextItem.model_validate(dumped)
    assert reparsed.ancestry is None


def test_context_item_empty_ancestry_round_trips() -> None:
    item = ContextItem.model_validate({**REQUIRED_ITEM, "ancestry": []})
    dumped = item.model_dump(by_alias=True)
    assert dumped["ancestry"] == []
    reparsed = ContextItem.model_validate(dumped)
    assert reparsed.ancestry == []


def test_context_item_rich_ancestry_keeps_display_name_wire_field() -> None:
    item = ContextItem.model_validate({**REQUIRED_ITEM, "ancestry": RICH_ANCESTRY})
    dumped = item.model_dump(by_alias=True)
    assert dumped["orgId"] == "org-uuid-abc"
    assert dumped["dataPath"] == ["custom", "note-1"]
    assert dumped["createdAt"] == REQUIRED_ITEM["createdAt"]
    assert dumped["userFeedback"] == "neutral"
    assert "created_at" not in dumped
    assert dumped["ancestry"] == RICH_ANCESTRY
    assert "displayName" not in dumped["ancestry"][0]
    reparsed = ContextItem.model_validate(dumped)
    assert reparsed.ancestry is not None
    assert [entry.uid for entry in reparsed.ancestry] == ["seg-a", "seg-b"]
    assert [entry.display_name for entry in reparsed.ancestry] == ["A", "B"]
    assert [entry.type for entry in reparsed.ancestry] == ["container", None]


def test_lookup_row_ancestry_is_optional_and_round_trips() -> None:
    omitted = ContextItemLookupRow.model_validate(LOOKUP_REQUIRED)
    assert "ancestry" not in omitted.model_fields_set

    row = ContextItemLookupRow.model_validate({**LOOKUP_REQUIRED, "ancestry": RICH_ANCESTRY})
    dumped = row.model_dump(by_alias=True)
    assert dumped["ancestry"] == RICH_ANCESTRY
    assert "displayName" not in dumped["ancestry"][0]
    reparsed = ContextItemLookupRow.model_validate(dumped)
    assert reparsed.ancestry is not None
    assert [entry.display_name for entry in reparsed.ancestry] == ["A", "B"]


def test_existing_to_camel_aliases_are_unchanged() -> None:
    """Ancestry pin must not change unrelated fields that rely on alias_generator=to_camel."""
    agent = AgentSelectionEntryDto.model_validate({"agentId": 17, "priorityOrder": 1})
    agent_dump = agent.model_dump(by_alias=True)
    assert agent_dump["agentId"] == 17
    assert agent_dump["priorityOrder"] == 1
    assert "agent_id" not in agent_dump

    member = OrgMemberDto.model_validate(
        {
            "userId": "user_1",
            "firstName": "Ada",
            "lastName": "Lovelace",
            "email": "ada@example.com",
            "imageUrl": "https://example.com/ada.png",
            "role": "admin",
        }
    )
    member_dump = member.model_dump(by_alias=True)
    assert member_dump["userId"] == "user_1"
    assert "user_id" not in member_dump

    schedule = TriggerScheduleDto.model_validate(
        {"frequency": Frequency.daily, "timezone": "UTC", "timeOfDay": "09:00"}
    )
    schedule_dump = schedule.model_dump(by_alias=True)
    assert schedule_dump["timeOfDay"] == "09:00"
    assert "time_of_day" not in schedule_dump

    totals = UsageTotalsDto.model_validate(
        {"callCount": 1, "inputTokens": 2, "outputTokens": 3, "credits": 4}
    )
    totals_dump = totals.model_dump(by_alias=True)
    assert totals_dump["inputTokens"] == 2
    assert "input_tokens" not in totals_dump

    group = MemberGroupDto.model_validate(
        {
            "uid": "grp-1",
            "name": "Everyone",
            "description": "",
            "createdAt": "2026-01-01T00:00:00.000Z",
            "updatedAt": "2026-01-01T00:00:00.000Z",
        }
    )
    group_dump = group.model_dump(by_alias=True)
    assert group_dump["createdAt"] == "2026-01-01T00:00:00.000Z"
    assert "created_at" not in group_dump

    trigger = TriggerDto.model_validate({"triggerType": TriggerType.schedule})
    trigger_dump = trigger.model_dump(by_alias=True)
    assert trigger_dump["triggerType"] == TriggerType.schedule
    assert "trigger_type" not in trigger_dump
