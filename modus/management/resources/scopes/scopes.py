"""Create, update, and deploy scopes via the management client."""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Union

from modus._config import ModusConfig
from modus._generated.models import (
    DeployResponseDto,
    PatchSkillMcpConfigDto,
    ScopeDto,
    SkillMcpInterfaceConfigDto,
    TransferOwnershipDto,
)
from modus._generated.resources.management.scopes import (
    _AsyncScopesResourceBase,
    _ScopesResourceBase,
)
from modus._http import AsyncHttpClient, HttpClient
from modus._openapi_invoke import invoke_operation, invoke_operation_async
from modus._query import update_mask_query
from modus._retry import async_with_retry, with_retry
from modus._validation import validate_id
from modus.types.skills import Skill

from ...types.json_blob import JsonObjectListInput, dump_json_object_list
from ...types.toolset import ToolsetInput, dump_toolset
from .._access_config_write import (
    access_config_body_for_create,
    access_config_body_for_update,
)
from ._update_body import _ScopeCreateBody, _ScopeUpdateBody
from .conversations import (
    AsyncScopeConversationsResource,
    ScopeConversationsResource,
)
from .evaluations import (
    ScopeEvaluationsResource,
)
from .interfaces import AsyncScopeInterfacesResource, ScopeInterfacesResource
from .memories import AsyncScopeMemoriesResource, ScopeMemoriesResource
from .supervision import AsyncScopeSupervisionResource, ScopeSupervisionResource


def _parse_scope(raw: dict) -> Skill:
    return ScopeDto.model_validate(raw)


def _parse_deploy_scope(raw: Any) -> Skill:
    """Validate deploy envelope; return the published scope."""
    return DeployResponseDto.model_validate(raw).scope


class ScopesResource(_ScopesResourceBase):
    """
    Full CRUD access to Modus scopes.

    ``mgmt.scopes.list()`` → page of scopes
    ``mgmt.scopes.get(scope_id)`` → scope (with variation fields)
    ``mgmt.scopes.create(name, ...)`` → scope
    ``mgmt.scopes.update(scope_id, ...)`` → scope
    ``mgmt.scopes.deploy(scope_id)`` → scope
    ``mgmt.scopes.delete(scope_id)`` → None
    ``mgmt.scopes.conversations(scope_id).list()`` → page of conversations
    ``mgmt.scopes.conversations(scope_id).get(tid)`` → conversation
    """

    def __init__(
        self,
        http: HttpClient,
        config: ModusConfig,
    ) -> None:
        super().__init__(http, config)

    def conversations(self, scope_id: Union[int, str]) -> ScopeConversationsResource:
        """Return the conversations sub-resource scoped to ``scope_id``."""
        return ScopeConversationsResource(self._http, self._config, scope_id)

    def memories(self, scope_id: Union[int, str]) -> ScopeMemoriesResource:
        """Return the memories sub-resource scoped to ``scope_id``."""
        return ScopeMemoriesResource(self._http, self._config, scope_id)

    def evaluations(self, scope_id: Union[int, str]) -> ScopeEvaluationsResource:
        """Return the evaluations sub-resource scoped to ``scope_id``."""
        return ScopeEvaluationsResource(self._http, self._config, scope_id)

    def supervision(self, scope_id: Union[int, str]) -> ScopeSupervisionResource:
        """Return the supervision sub-resource scoped to ``scope_id``."""
        return ScopeSupervisionResource(self._http, self._config, scope_id)

    def interfaces(self, scope_id: Union[int, str]) -> ScopeInterfacesResource:
        """Return the Slack/Teams interfaces sub-resource scoped to ``scope_id``."""
        return ScopeInterfacesResource(self._http, self._config, scope_id)

    def create(
        self,
        name: str,
        *,
        description: Optional[str] = None,
        expected_output: Optional[str] = None,
        instructions: Optional[List[str]] = None,
        toolset: Optional[ToolsetInput] = None,
        model: Optional[str] = None,
        connection_set: Optional[JsonObjectListInput] = None,
        context_selections: Optional[JsonObjectListInput] = None,
        include_own_learnings: Optional[bool] = None,
        interfaces: Optional[JsonObjectListInput] = None,
        guardrails: Optional[List[str]] = None,
    ) -> Skill:
        """Create a new Modus scope in the organisation.

        Args:
            name: Display name for the scope.
            description: Optional human-readable description.
            expected_output: Optional expected-output guidance for the model.
            instructions: Optional instruction strings.
            toolset: Optional tool configuration payload.
            model: Optional model id (for example ``\"claude-sonnet-5\"``).
            connection_set: Optional data connections for the scope.
            context_selections: Optional context selection payload.
            include_own_learnings: Whether the scope reads what is taught while
                using it. Defaults to ``True`` on the server.
            interfaces: Optional MCP interface configuration. Only entries with
                ``type: "mcp"`` are accepted; any other type makes the call raise
                ``ModusError`` (HTTP 400).
            guardrails: Runtime guardrail labels (for example ``\"no-pii\"``).
                When set, the scope is created with these labels under the
                organisation default sharing rules. Omit (``None``) to create
                with no guardrails. ACL fields cannot be set from the SDK.

        Returns:
            The new scope (draft) with ``id``, ``name``, and related fields.

        Example:
            >>> mgmt = modus.management.ModusManagement()
            >>> scope = mgmt.scopes.create(
            ...     name="Support assistant",
            ...     model="claude-sonnet-5",
            ... )
            >>> print(scope.id, scope.name)
        """
        body = _ScopeCreateBody(
            name=name, description=description, expected_output=expected_output,
            instructions=instructions,
            toolset=dump_toolset(toolset),
            model=model,
            connection_set=dump_json_object_list(connection_set, field_name="connection_set"),
            context_selections=dump_json_object_list(
                context_selections, field_name="context_selections"
            ),
            include_own_learnings=include_own_learnings,
            interfaces=dump_json_object_list(interfaces, field_name="interfaces"),
            access_config=access_config_body_for_create(guardrails),
        ).model_dump(by_alias=True, exclude_none=True)
        raw = with_retry(
            lambda: invoke_operation(
                self._http, "ScopesController_create", json_body=body
            ),
            self._config.max_retries,
        )
        return _parse_scope(raw)

    def update(
        self,
        scope_id: Union[int, str],
        *,
        name: Optional[str] = None,
        description: Optional[str] = None,
        expected_output: Optional[str] = None,
        instructions: Optional[List[str]] = None,
        toolset: Optional[ToolsetInput] = None,
        model: Optional[str] = None,
        connection_set: Optional[JsonObjectListInput] = None,
        context_selections: Optional[JsonObjectListInput] = None,
        interfaces: Optional[JsonObjectListInput] = None,
        guardrails: Optional[List[str]] = None,
        manager_id: Optional[str] = None,
        evaluations: Optional[JsonObjectListInput] = None,
        supervision_subordinate_descriptions: Optional[Dict[str, str]] = None,
        update_mask: Optional[str] = None,
    ) -> Skill:
        """Update a Modus scope's configuration.

        Only the fields you pass are changed. To clear a field, name it in
        ``update_mask`` (a comma-separated list of field names) and leave its
        argument unset — the server sets each masked field to null and leaves
        fields not named in the mask untouched.

        Args:
            scope_id: Scope numeric id or slug string.
            name: Optional new display name.
            description: Optional new description.
            expected_output: Optional expected-output guidance.
            instructions: Optional instruction strings.
            toolset: Optional tool configuration payload.
            model: Optional model id.
            connection_set: Optional data connections for the scope.
            context_selections: Optional context selection payload.
            interfaces: Optional MCP interface configuration. Only entries with
                ``type: "mcp"`` are accepted; any other type makes the call raise
                ``ModusError`` (HTTP 400).
            guardrails: Runtime guardrail labels to set on the scope. Fetches
                the current scope first and merges these labels into its access
                configuration (an extra ``get`` request). Omit (``None``) to
                leave guardrails unchanged. Pass ``[]`` to clear all guardrails.
            manager_id: Optional supervising manager scope id.
            evaluations: Optional evaluation configuration payload.
            supervision_subordinate_descriptions: Optional map of subordinate
                scope id to description text.
            update_mask: Comma-separated field names to update or clear.

        Returns:
            The updated scope.

        Example:
            >>> mgmt = modus.management.ModusManagement()
            >>> scope = mgmt.scopes.update(
            ...     "PLACEHOLDER_SCOPE_ID",
            ...     description="Answers billing questions for enterprise customers.",
            ... )
            >>> scope.description
        """
        validate_id(scope_id, name="scope_id")
        access_config = access_config_body_for_update(
            guardrails,
            lambda: with_retry(
                lambda: invoke_operation(
                    self._http,
                    "ScopesController_get",
                    path_params={"id": scope_id},
                ),
                self._config.max_retries,
            ),
        )
        body = _ScopeUpdateBody(
            name=name, description=description, expected_output=expected_output,
            instructions=instructions,
            toolset=dump_toolset(toolset),
            model=model,
            connection_set=dump_json_object_list(connection_set, field_name="connection_set"),
            context_selections=dump_json_object_list(
                context_selections, field_name="context_selections"
            ),
            interfaces=dump_json_object_list(interfaces, field_name="interfaces"),
            access_config=access_config,
            manager_id=manager_id,
            evaluations=dump_json_object_list(evaluations, field_name="evaluations"),
            supervision_subordinate_descriptions=supervision_subordinate_descriptions,
        ).model_dump(by_alias=True, exclude_none=update_mask is None)
        raw = with_retry(
            lambda: invoke_operation(
                self._http,
                "ScopesController_update",
                path_params={"id": scope_id},
                query=update_mask_query(update_mask),
                json_body=body,
            ),
            self._config.max_retries,
        )
        return _parse_scope(raw)

    def deploy(self, scope_id: Union[int, str]) -> Skill:
        """Publish the current draft of a Modus scope.

        Args:
            scope_id: Scope to publish.

        Returns:
            The scope with its newly published configuration.

        Example:
            >>> scope = mgmt.scopes.create(name="Support assistant")
            >>> published = mgmt.scopes.deploy(scope.id)
            >>> published.status
        """
        validate_id(scope_id, name="scope_id")
        raw = with_retry(
            lambda: invoke_operation(
                self._http,
                "ScopesController_deploy",
                path_params={"id": scope_id},
                json_body={},
            ),
            self._config.max_retries,
            retry_not_found_on_deploy=True,
        )
        return _parse_deploy_scope(raw)

    def request_ownership_transfer(
        self, scope_id: Union[int, str], *, new_owner_user_id: str,
    ) -> Skill:
        """Start transferring ownership of a scope to another organisation member."""
        validate_id(scope_id, name="scope_id")
        body = TransferOwnershipDto(new_owner_user_id=new_owner_user_id)
        raw = with_retry(
            lambda: invoke_operation(
                self._http,
                "ScopesController_requestOwnershipTransfer",
                path_params={"id": scope_id},
                json_body=body.model_dump(by_alias=True, exclude_none=True),
            ),
            self._config.max_retries,
        )
        return _parse_scope(raw)

    def patch_mcp_config(
        self, scope_id: Union[int, str], *, mcp_config: Dict[str, Any],
    ) -> None:
        """Update MCP server configuration for a scope."""
        validate_id(scope_id, name="scope_id")
        body = PatchSkillMcpConfigDto(
            config=SkillMcpInterfaceConfigDto.model_validate(mcp_config)
        )
        with_retry(
            lambda: invoke_operation(
                self._http,
                "ScopesController_patchMcpConfig",
                path_params={"id": scope_id},
                json_body=body.model_dump(by_alias=True, exclude_none=True),
            ),
            self._config.max_retries,
        )

    def get_variation(
        self, scope_id: Union[int, str], *, variation_uid: str,
    ) -> Skill:
        """Retrieve a historic version snapshot of a scope."""
        validate_id(scope_id, name="scope_id")
        validate_id(variation_uid, name="variation_uid")
        raw = with_retry(
            lambda: invoke_operation(
                self._http,
                "ScopesController_getVariation",
                path_params={"id": scope_id, "variationUid": variation_uid},
            ),
            self._config.max_retries,
        )
        return _parse_scope(raw)


class AsyncScopesResource(_AsyncScopesResourceBase):
    def __init__(
        self,
        http: AsyncHttpClient,
        config: ModusConfig,
    ) -> None:
        super().__init__(http, config)

    def conversations(self, scope_id: Union[int, str]) -> AsyncScopeConversationsResource:
        """Return the conversations sub-resource scoped to ``scope_id``."""
        return AsyncScopeConversationsResource(self._http, self._config, scope_id)

    def memories(self, scope_id: Union[int, str]) -> AsyncScopeMemoriesResource:
        """Return the memories sub-resource scoped to ``scope_id``."""
        return AsyncScopeMemoriesResource(self._http, self._config, scope_id)

    def supervision(self, scope_id: Union[int, str]) -> AsyncScopeSupervisionResource:
        """Return the supervision sub-resource scoped to ``scope_id``."""
        return AsyncScopeSupervisionResource(self._http, self._config, scope_id)

    def interfaces(self, scope_id: Union[int, str]) -> AsyncScopeInterfacesResource:
        """Return the Slack/Teams interfaces sub-resource scoped to ``scope_id``."""
        return AsyncScopeInterfacesResource(self._http, self._config, scope_id)

    async def create(
        self, name: str, *,
        description: Optional[str] = None, expected_output: Optional[str] = None,
        instructions: Optional[List[str]] = None,
        toolset: Optional[ToolsetInput] = None,
        model: Optional[str] = None,
        connection_set: Optional[JsonObjectListInput] = None,
        context_selections: Optional[JsonObjectListInput] = None,
        include_own_learnings: Optional[bool] = None,
        interfaces: Optional[JsonObjectListInput] = None,
        guardrails: Optional[List[str]] = None,
    ) -> Skill:
        """Create a new Modus scope in the organisation.

        Args:
            include_own_learnings: Whether the scope reads what is taught while
                using it. Defaults to ``True`` on the server.
            guardrails: Runtime guardrail labels (for example ``\"no-pii\"``).
                When set, the scope is created with these labels under the
                organisation default sharing rules. Omit (``None``) to create
                with no guardrails. ACL fields cannot be set from the SDK.
        """
        body = _ScopeCreateBody(
            name=name, description=description, expected_output=expected_output,
            instructions=instructions,
            toolset=dump_toolset(toolset),
            model=model,
            connection_set=dump_json_object_list(connection_set, field_name="connection_set"),
            context_selections=dump_json_object_list(
                context_selections, field_name="context_selections"
            ),
            include_own_learnings=include_own_learnings,
            interfaces=dump_json_object_list(interfaces, field_name="interfaces"),
            access_config=access_config_body_for_create(guardrails),
        ).model_dump(by_alias=True, exclude_none=True)
        raw = await async_with_retry(
            lambda: invoke_operation_async(
                self._http, "ScopesController_create", json_body=body
            ),
            self._config.max_retries,
        )
        return _parse_scope(raw)

    async def update(
        self, scope_id: Union[int, str], *,
        name: Optional[str] = None, description: Optional[str] = None,
        expected_output: Optional[str] = None, instructions: Optional[List[str]] = None,
        toolset: Optional[ToolsetInput] = None,
        model: Optional[str] = None,
        connection_set: Optional[JsonObjectListInput] = None,
        context_selections: Optional[JsonObjectListInput] = None,
        interfaces: Optional[JsonObjectListInput] = None,
        guardrails: Optional[List[str]] = None,
        manager_id: Optional[str] = None,
        evaluations: Optional[JsonObjectListInput] = None,
        supervision_subordinate_descriptions: Optional[Dict[str, str]] = None,
        update_mask: Optional[str] = None,
    ) -> Skill:
        """Update a Modus scope's configuration.

        Only the fields you pass are changed. To clear a field, name it in
        ``update_mask`` (a comma-separated list of field names) and leave its
        argument unset — the server sets each masked field to null and leaves
        fields not named in the mask untouched.

        Args:
            guardrails: Runtime guardrail labels to set on the scope. Fetches
                the current scope first and merges these labels into its access
                configuration (an extra ``get`` request). Omit (``None``) to
                leave guardrails unchanged. Pass ``[]`` to clear all guardrails.
        """
        validate_id(scope_id, name="scope_id")
        if guardrails is not None:
            existing = await async_with_retry(
                lambda: invoke_operation_async(
                    self._http,
                    "ScopesController_get",
                    path_params={"id": scope_id},
                ),
                self._config.max_retries,
            )
            access_config = access_config_body_for_update(guardrails, lambda: existing)
        else:
            access_config = None
        body = _ScopeUpdateBody(
            name=name, description=description, expected_output=expected_output,
            instructions=instructions,
            toolset=dump_toolset(toolset),
            model=model,
            connection_set=dump_json_object_list(connection_set, field_name="connection_set"),
            context_selections=dump_json_object_list(
                context_selections, field_name="context_selections"
            ),
            interfaces=dump_json_object_list(interfaces, field_name="interfaces"),
            access_config=access_config,
            manager_id=manager_id,
            evaluations=dump_json_object_list(evaluations, field_name="evaluations"),
            supervision_subordinate_descriptions=supervision_subordinate_descriptions,
        ).model_dump(by_alias=True, exclude_none=update_mask is None)
        raw = await async_with_retry(
            lambda: invoke_operation_async(
                self._http,
                "ScopesController_update",
                path_params={"id": scope_id},
                query=update_mask_query(update_mask),
                json_body=body,
            ),
            self._config.max_retries,
        )
        return _parse_scope(raw)

    async def deploy(self, scope_id: Union[int, str]) -> Skill:
        """Publish the current draft of a Modus scope. See the sync ``deploy`` for argument details."""
        validate_id(scope_id, name="scope_id")
        raw = await async_with_retry(
            lambda: invoke_operation_async(
                self._http,
                "ScopesController_deploy",
                path_params={"id": scope_id},
                json_body={},
            ),
            self._config.max_retries,
            retry_not_found_on_deploy=True,
        )
        return _parse_deploy_scope(raw)

    async def request_ownership_transfer(
        self, scope_id: Union[int, str], *, new_owner_user_id: str,
    ) -> Skill:
        """Start transferring ownership of a scope to another organisation member."""
        validate_id(scope_id, name="scope_id")
        body = TransferOwnershipDto(new_owner_user_id=new_owner_user_id)
        raw = await async_with_retry(
            lambda: invoke_operation_async(
                self._http,
                "ScopesController_requestOwnershipTransfer",
                path_params={"id": scope_id},
                json_body=body.model_dump(by_alias=True, exclude_none=True),
            ),
            self._config.max_retries,
        )
        return _parse_scope(raw)

    async def patch_mcp_config(
        self, scope_id: Union[int, str], *, mcp_config: Dict[str, Any],
    ) -> None:
        """Update MCP server configuration for a scope."""
        validate_id(scope_id, name="scope_id")
        body = PatchSkillMcpConfigDto(
            config=SkillMcpInterfaceConfigDto.model_validate(mcp_config)
        )
        await async_with_retry(
            lambda: invoke_operation_async(
                self._http,
                "ScopesController_patchMcpConfig",
                path_params={"id": scope_id},
                json_body=body.model_dump(by_alias=True, exclude_none=True),
            ),
            self._config.max_retries,
        )

    async def get_variation(
        self, scope_id: Union[int, str], *, variation_uid: str,
    ) -> Skill:
        """Retrieve a historic version snapshot of a scope."""
        validate_id(scope_id, name="scope_id")
        validate_id(variation_uid, name="variation_uid")
        raw = await async_with_retry(
            lambda: invoke_operation_async(
                self._http,
                "ScopesController_getVariation",
                path_params={"id": scope_id, "variationUid": variation_uid},
            ),
            self._config.max_retries,
        )
        return _parse_scope(raw)
