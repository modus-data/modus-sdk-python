"""Wire models for agent triggers — mirrors TriggerDto / TriggerScheduleDto."""
from __future__ import annotations

from typing import List, Literal, Optional

from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel

ScheduleFrequencyWire = Literal["hourly", "daily", "weekly", "monthly", "custom"]
TriggerTypeWire = Literal["schedule", "webhook", "api", "slack", "manual"]
WeekdayWire = Literal[
    "monday",
    "tuesday",
    "wednesday",
    "thursday",
    "friday",
    "saturday",
    "sunday",
]


class _TriggerScheduleWire(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        extra="ignore",
    )

    frequency: ScheduleFrequencyWire
    time_of_day: Optional[str] = None
    timezone: str
    weekdays: Optional[List[WeekdayWire]] = None
    day_of_month: Optional[int] = None
    cron_expressions: Optional[List[str]] = None
    cron_description: Optional[str] = None


class _TriggerWire(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        extra="ignore",
    )

    trigger_type: TriggerTypeWire
    schedule: Optional[_TriggerScheduleWire] = None
