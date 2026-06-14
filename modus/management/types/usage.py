"""Usage reporting types (re-exported from ListUsageResponseDto)."""

from modus._generated.models import (
    ListUsageResponseDto,
    UsageBucketDto,
    UsageTotalsDto,
)

UsageBucket = UsageBucketDto
UsageTotals = UsageTotalsDto
UsageReport = ListUsageResponseDto

__all__ = ["UsageBucket", "UsageTotals", "UsageReport"]
