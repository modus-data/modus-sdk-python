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


def test_parse_trigger_from_get_model_serializes_snake_case_request() -> None:
    """GET returns WorkflowTriggerResponseDto; update still sends snake_case keys."""
    from modus._generated.models import AgentVariationDto

    manual = AgentVariationDto.model_validate(
        {"trigger": {"trigger_type": "manual", "schedule": None}}
    )
    assert manual.trigger is not None
    manual_trigger = parse_trigger(manual.trigger)
    assert isinstance(manual_trigger, ManualTrigger)
    assert dump_trigger(manual_trigger) == {"trigger_type": "manual"}

    scheduled = AgentVariationDto.model_validate(
        {
            "trigger": {
                "trigger_type": "schedule",
                "schedule": {
                    "frequency": "daily",
                    "time_of_day": "09:00",
                    "timezone": "UTC",
                    "weekdays": None,
                    "day_of_month": None,
                    "cron_expressions": None,
                    "cron_description": None,
                },
            }
        }
    )
    assert scheduled.trigger is not None
    schedule_trigger = parse_trigger(scheduled.trigger)
    assert isinstance(schedule_trigger, ScheduleTrigger)
    dumped = dump_trigger(schedule_trigger)
    assert dumped is not None
    assert dumped["trigger_type"] == "schedule"
    assert dumped["schedule"]["frequency"] == "daily"
    assert dumped["schedule"]["time_of_day"] == "09:00"
    assert dumped["schedule"]["timezone"] == "UTC"
    assert "timeOfDay" not in dumped["schedule"]
    assert "triggerType" not in dumped


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


# Reading a Workflow that starts on email must not raise "unsupported trigger_type".
def test_parse_email_trigger_and_dump_it_back() -> None:
    raw = {
        "trigger_type": "email",
        "schedule": None,
        "email": {"sender_policy": "allowlist", "allowed_senders": ["@acme.com"]},
    }
    parsed = parse_trigger(raw)
    assert parsed == AgentTrigger.email(allowed_senders=["@acme.com"])
    assert dump_trigger(parsed) == {
        "trigger_type": "email",
        "email": {"sender_policy": "allowlist", "allowed_senders": ["@acme.com"]},
    }
