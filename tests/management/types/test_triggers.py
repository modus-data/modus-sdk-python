"""Tests for AgentTrigger typed models and factories."""

import pytest
from modus.management.types.triggers import (
    AgentTrigger,
    ManualTrigger,
    ScheduleTrigger,
    TriggerSchedule,
    dump_trigger,
    parse_trigger,
)
from pydantic import ValidationError


def test_schedule_daily_factory() -> None:
    trigger = AgentTrigger.schedule_daily(time="09:00", timezone="UTC")
    assert isinstance(trigger, ScheduleTrigger)
    assert trigger.trigger_type == "schedule"
    assert trigger.schedule.frequency == "daily"
    assert trigger.schedule.time_of_day == "09:00"


def test_manual_factory() -> None:
    trigger = AgentTrigger.manual()
    assert isinstance(trigger, ManualTrigger)
    assert trigger.trigger_type == "manual"


def test_weekly_requires_weekdays() -> None:
    with pytest.raises(ValidationError):
        TriggerSchedule(frequency="weekly", time_of_day="09:00", timezone="UTC")


def test_dump_trigger_snake_case() -> None:
    payload = dump_trigger(AgentTrigger.manual())
    assert payload == {"trigger_type": "manual"}


def test_dump_trigger_rejects_raw_dict() -> None:
    with pytest.raises(TypeError, match="AgentTrigger"):
        dump_trigger({"trigger_type": "manual"})


def test_parse_trigger_schedule_without_client_validation() -> None:
    """Inbound API payloads skip cadence validators (wire may omit optional fields)."""
    raw = {
        "triggerType": "schedule",
        "schedule": {
            "frequency": "daily",
            "timezone": "UTC",
        },
    }
    trigger = parse_trigger(raw)
    assert isinstance(trigger, ScheduleTrigger)
    assert trigger.schedule.frequency == "daily"
    assert trigger.schedule.time_of_day is None


def test_parse_trigger_round_trip() -> None:
    raw = {
        "triggerType": "schedule",
        "schedule": {
            "frequency": "daily",
            "timeOfDay": "09:00",
            "timezone": "America/New_York",
        },
    }
    trigger = parse_trigger(raw)
    assert isinstance(trigger, ScheduleTrigger)
    assert trigger.schedule.timezone == "America/New_York"
    dumped = dump_trigger(trigger)
    assert dumped["trigger_type"] == "schedule"
    assert dumped["schedule"]["time_of_day"] == "09:00"
