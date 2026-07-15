"""List organization members and member groups."""

from __future__ import annotations

from modus._config import ModusConfig
from modus._generated.models import (
    ListMemberGroupsResponseDto,
    ListOrgMembersResponseDto,
    MemberGroupDto,
    OrgMemberDto,
)
from modus._http import AsyncHttpClient, HttpClient
from modus._openapi_invoke import invoke_operation, invoke_operation_async
from modus._retry import async_with_retry, with_retry


class UsersResource:
    def __init__(self, http: HttpClient, config: ModusConfig) -> None:
        self._http, self._config = http, config

    def list_member_groups(self) -> list[MemberGroupDto]:
        """List member groups in the organization."""
        raw = with_retry(
            lambda: invoke_operation(self._http, "MemberGroupsController_list"),
            self._config.max_retries,
        )
        return ListMemberGroupsResponseDto.model_validate(raw).groups

    def list_org_members(self) -> list[OrgMemberDto]:
        """List organization members."""
        raw = with_retry(
            lambda: invoke_operation(self._http, "OrgMembersController_list"),
            self._config.max_retries,
        )
        return ListOrgMembersResponseDto.model_validate(raw).members


class AsyncUsersResource:
    def __init__(self, http: AsyncHttpClient, config: ModusConfig) -> None:
        self._http, self._config = http, config

    async def list_member_groups(self) -> list[MemberGroupDto]:
        """List member groups in the organization."""
        raw = await async_with_retry(
            lambda: invoke_operation_async(self._http, "MemberGroupsController_list"),
            self._config.max_retries,
        )
        return ListMemberGroupsResponseDto.model_validate(raw).groups

    async def list_org_members(self) -> list[OrgMemberDto]:
        """List organization members."""
        raw = await async_with_retry(
            lambda: invoke_operation_async(self._http, "OrgMembersController_list"),
            self._config.max_retries,
        )
        return ListOrgMembersResponseDto.model_validate(raw).members
