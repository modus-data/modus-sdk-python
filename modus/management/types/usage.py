"""Usage reporting types (re-exported from ListUsageResponseDto)."""

from modus._generated.models import (
    ListUsageResponseDto,
    ListUsageUsersResponseDto,
    UsageBucketDto,
    UsageTotalsDto,
    UsageUserDto,
)

UsageBucket = UsageBucketDto
UsageTotals = UsageTotalsDto
UsageReport = ListUsageResponseDto
UsageUser = UsageUserDto
UsageUsersReport = ListUsageUsersResponseDto

__all__ = [
    "UsageBucket",
    "UsageTotals",
    "UsageReport",
    "UsageUser",
    "UsageUsersReport",
]
