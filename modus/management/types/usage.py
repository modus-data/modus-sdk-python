"""Usage reporting types (wire shape from ListUsageResponseDto)."""

from __future__ import annotations

from typing import List

from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel


class UsageBucket(BaseModel):
    """One time-bucket of LLM usage for a model."""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        extra="ignore",
    )

    bucket: str
    model: str
    call_count: int
    input_tokens: int
    output_tokens: int


class UsageTotals(BaseModel):
    """Aggregated token and call counts across the query window."""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        extra="ignore",
    )

    call_count: int
    input_tokens: int
    output_tokens: int


class UsageReport(BaseModel):
    """LLM usage rollups for your organisation over a time window."""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        extra="ignore",
    )

    org_id: str
    since: str
    until: str
    rollup: str
    buckets: List[UsageBucket]
    totals: UsageTotals
