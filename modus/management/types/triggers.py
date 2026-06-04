"""Agent trigger types — Option B (Pydantic models + factories)."""
from __future__ import annotations

import warnings
from typing import Any, Dict, List, Literal, Optional, Union

from pydantic import BaseModel, ConfigDict, Field, model_validator
from pydantic.alias_generators import to_camel

from .._wire.triggers import _TriggerWire

ScheduleFrequency = Literal["hourly", "daily", "weekly", "monthly", "custom"]
TriggerType = Literal["schedule", "webhook", "api", "slack", "manual"]
Weekday = Literal[
    "monday",
    "tuesday",
    "wednesday",
    "thursday",
    "friday",
    "saturday",
    "sunday",
]


class TriggerSchedule(BaseModel):
    """Schedule cadence for a scheduled agent trigger."""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        extra="forbid",
    )

    frequency: ScheduleFrequency
    timezone: str
    time_of_day: Optional[str] = Field(
        default=None,
        description="24-hour HH:MM. Required for hourly, daily, weekly, and monthly.",
    )
    weekdays: Optional[List[Weekday]] = Field(
        default=None,
        description="Required when frequency is weekly.",
    )
    day_of_month: Optional[int] = Field(
        default=None,
        ge=1,
        le=31,
        description="Required when frequency is monthly.",
    )
    cron_expressions: Optional[List[str]] = Field(
        default=None,
        description="Required when frequency is custom.",
    )
    cron_description: Optional[str] = Field(
        default=None,
        description="Human-readable description when frequency is custom.",
    )

    @model_validator(mode="after")
    def _validate_cadence(self) -> TriggerSchedule:
        freq = self.frequency
        if freq in ("hourly", "daily", "weekly", "monthly") and not self.time_of_day:
            raise ValueError(f"time_of_day is required when frequency is {freq!r}")
        if freq == "weekly" and not self.weekdays:
            raise ValueError("weekdays is required when frequency is 'weekly'")
        if freq == "monthly" and self.day_of_month is None:
            raise ValueError("day_of_month is required when frequency is 'monthly'")
        if freq == "custom":
            if not self.cron_expressions:
                raise ValueError("cron_expressions is required when frequency is 'custom'")
            if not self.cron_description:
                raise ValueError("cron_description is required when frequency is 'custom'")
        return self


class ScheduleTrigger(BaseModel):
    """Agent runs on a schedule."""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        extra="forbid",
    )

    trigger_type: Literal["schedule"] = "schedule"
    schedule: TriggerSchedule


class ManualTrigger(BaseModel):
    """Agent is started manually (no automatic schedule)."""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        extra="forbid",
    )

    trigger_type: Literal["manual"] = "manual"


class WebhookTrigger(BaseModel):
    """Agent is invoked via webhook."""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        extra="forbid",
    )

    trigger_type: Literal["webhook"] = "webhook"


class ApiTrigger(BaseModel):
    """Agent is invoked via API."""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        extra="forbid",
    )

    trigger_type: Literal["api"] = "api"


class SlackTrigger(BaseModel):
    """Agent is invoked from Slack."""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        extra="forbid",
    )

    trigger_type: Literal["slack"] = "slack"


AgentTriggerValue = Union[
    ScheduleTrigger,
    ManualTrigger,
    WebhookTrigger,
    ApiTrigger,
    SlackTrigger,
]

TriggerInput = Union[AgentTriggerValue, Dict[str, Any]]


def dump_trigger(value: Optional[TriggerInput]) -> Optional[Dict[str, Any]]:
    """Serialize a trigger for the HTTP request body."""
    if value is None:
        return None
    if isinstance(value, dict):
        warnings.warn(
            "Passing a raw dict for trigger= is deprecated; use AgentTrigger.manual() "
            "or other typed triggers from modus.management.types.",
            DeprecationWarning,
            stacklevel=3,
        )
        return value
    # The agents API validates the trigger blob with snake_case keys
    # (trigger_type, schedule.time_of_day, ...), unlike the camelCase top-level
    # body. Dump by field name so AgentTrigger.* matches TriggerDto.
    return value.model_dump(by_alias=False, exclude_none=True)


def parse_trigger(raw: object) -> Optional[AgentTriggerValue]:
    """Parse trigger JSON from a variation or API response."""
    if raw is None:
        return None
    wire = _TriggerWire.model_validate(raw)
    if wire.trigger_type == "schedule":
        if wire.schedule is None:
            raise ValueError("schedule is required when trigger_type is 'schedule'")
        return ScheduleTrigger.model_construct(
            trigger_type="schedule",
            schedule=TriggerSchedule.model_construct(
                **wire.schedule.model_dump(by_alias=False)
            ),
        )
    if wire.trigger_type == "manual":
        return ManualTrigger()
    if wire.trigger_type == "webhook":
        return WebhookTrigger()
    if wire.trigger_type == "api":
        return ApiTrigger()
    if wire.trigger_type == "slack":
        return SlackTrigger()
    raise ValueError(f"unsupported trigger_type: {wire.trigger_type!r}")


class AgentTrigger:
    """
    Factory helpers for agent triggers.

    Use ``trigger=AgentTrigger.schedule_daily(...)`` on ``mgmt.agents.create`` /
    ``update``. For full control, construct ``ScheduleTrigger`` or ``ManualTrigger``
    directly.
    """

    @classmethod
    def manual(cls) -> ManualTrigger:
        return ManualTrigger()

    @classmethod
    def webhook(cls) -> WebhookTrigger:
        return WebhookTrigger()

    @classmethod
    def api(cls) -> ApiTrigger:
        return ApiTrigger()

    @classmethod
    def slack(cls) -> SlackTrigger:
        return SlackTrigger()

    @classmethod
    def schedule_daily(cls, *, time: str, timezone: str) -> ScheduleTrigger:
        return ScheduleTrigger(
            schedule=TriggerSchedule(
                frequency="daily",
                time_of_day=time,
                timezone=timezone,
            )
        )

    @classmethod
    def schedule_weekly(
        cls,
        *,
        time: str,
        timezone: str,
        weekdays: List[Weekday],
    ) -> ScheduleTrigger:
        return ScheduleTrigger(
            schedule=TriggerSchedule(
                frequency="weekly",
                time_of_day=time,
                timezone=timezone,
                weekdays=weekdays,
            )
        )

    @classmethod
    def schedule_monthly(
        cls,
        *,
        time: str,
        timezone: str,
        day_of_month: int,
    ) -> ScheduleTrigger:
        return ScheduleTrigger(
            schedule=TriggerSchedule(
                frequency="monthly",
                time_of_day=time,
                timezone=timezone,
                day_of_month=day_of_month,
            )
        )

    @classmethod
    def schedule_hourly(cls, *, time: str, timezone: str) -> ScheduleTrigger:
        return ScheduleTrigger(
            schedule=TriggerSchedule(
                frequency="hourly",
                time_of_day=time,
                timezone=timezone,
            )
        )

    @classmethod
    def schedule_custom(
        cls,
        *,
        cron_expressions: List[str],
        timezone: str,
        cron_description: str,
    ) -> ScheduleTrigger:
        return ScheduleTrigger(
            schedule=TriggerSchedule(
                frequency="custom",
                timezone=timezone,
                cron_expressions=cron_expressions,
                cron_description=cron_description,
            )
        )
