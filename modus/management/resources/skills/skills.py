"""Skills resource — /api/v1/skills (full CRUD, management SDK)"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Union
from urllib.parse import quote

from modus._config import ModusConfig
from modus._http import AsyncHttpClient, HttpClient
from modus._pagination import aip_list_params, build_aip_page_mapped, build_async_aip_page_mapped
from modus._query import with_update_mask as _with_update_mask
from modus._retry import async_with_retry, with_retry
from modus._validation import validate_id, validate_page_size
from modus.types.pagination import AsyncPage, Page
from modus.types.views import VariationView

from ..._wire.skills import _SkillWire
from ...types.json_blob import JsonObjectListInput, dump_json_object_list
from ...types.skills import Skill
from ...types.toolset import ToolsetInput, dump_toolset
from .._access_config_write import (
    access_config_body_for_create,
    access_config_body_for_update,
)
from ._translate import _translate_skill
from ._update_body import _SkillCreateBody, _SkillUpdateBody
from .conversations import AsyncConversationsResource, ConversationsResource
from .memories import AsyncMemoriesResource, MemoriesResource


def _map_skill(raw: dict) -> Skill:
    return _translate_skill(_SkillWire.model_validate(raw))


def _parse_skill_response(raw: object) -> Skill:
    skill_data = raw.get("skill", raw) if isinstance(raw, dict) else raw
    return _translate_skill(_SkillWire.model_validate(skill_data))


def _skills_list_params(
    page_size: int,
    page_token: Optional[str],
    search: Optional[str],
    view: Optional[VariationView],
    manager_id: Optional[int],
) -> dict:
    extra: dict = {}
    if search is not None:
        extra["search"] = search
    if view is not None:
        extra["view"] = view
    if manager_id is not None:
        extra["managerId"] = manager_id
    return aip_list_params(page_size, page_token, **extra)


class SkillsResource:
    """
    Full CRUD access to Modus skills.

    mgmt.skills.list()                              → Page[Skill]
    mgmt.skills.get(skill_id)                       → Skill (with variation fields)
    mgmt.skills.create(name, *, ...)                → Skill
    mgmt.skills.update(skill_id, *, ...)            → Skill
    mgmt.skills.deploy(skill_id)                    → Skill
    mgmt.skills.delete(skill_id)                    → None
    mgmt.skills.conversations(skill_id).list()      → Page[ConversationListItem]
    mgmt.skills.conversations(skill_id).get(tid)    → Conversation
    """

    def __init__(self, http: HttpClient, config: ModusConfig) -> None:
        self._http = http
        self._config = config

    def conversations(self, skill_id: Union[int, str]) -> ConversationsResource:
        """Return the conversations sub-resource scoped to ``skill_id``."""
        return ConversationsResource(self._http, self._config, skill_id)

    def memories(self, skill_id: Union[int, str]) -> MemoriesResource:
        """Return the memories sub-resource scoped to ``skill_id``."""
        return MemoriesResource(self._http, self._config, skill_id)

    def list(
        self,
        *,
        page_size: int = 25,
        page_token: Optional[str] = None,
        search: Optional[str] = None,
        view: Optional[VariationView] = None,
        manager_id: Optional[int] = None,
    ) -> Page[Skill]:
        """
        List all Modus skills in the organisation.

        Args:
            page_size:   Maximum number of items to return (default 25).
            page_token:  Token from a previous page's ``next_page_token``; omit for the first page.
            search:      Case-insensitive substring filter on the skill name.
            view:        Variation view — ``"active"`` (deployed) or ``"draft"``.
            manager_id:  Return only skills supervised by this manager skill id.
        """
        validate_page_size(page_size)
        return self._list_page(page_size, page_token, search, view, manager_id)

    def _list_page(
        self,
        page_size: int,
        page_token: Optional[str],
        search: Optional[str] = None,
        view: Optional[VariationView] = None,
        manager_id: Optional[int] = None,
    ) -> Page[Skill]:
        params = _skills_list_params(page_size, page_token, search, view, manager_id)
        data = with_retry(
            lambda: self._http.get("/api/v1/skills", params=params),
            self._config.max_retries,
        )
        return build_aip_page_mapped(
            data,
            "skills",
            _map_skill,
            lambda cur: self._list_page(page_size, cur, search, view, manager_id),
        )

    def get(
        self,
        skill_id: Union[int, str],
        *,
        view: Optional[VariationView] = None,
    ) -> Skill:
        """Retrieve a Modus skill with full configuration (instructions, model, and related fields)."""
        validate_id(skill_id, name="skill_id")
        safe_id = quote(str(skill_id), safe="")
        params = {} if view is None else {"view": view}
        data = with_retry(
            lambda: self._http.get(f"/api/v1/skills/{safe_id}", params=params or None),
            self._config.max_retries,
        )
        return _translate_skill(_SkillWire.model_validate(data))

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
        interfaces: Optional[JsonObjectListInput] = None,
        guardrails: Optional[List[str]] = None,
    ) -> Skill:
        """Create a new Modus skill in the organisation.

        Args:
            guardrails: Runtime guardrail labels (for example ``\"no-pii\"``).
                When set, the skill is created with these labels under the
                organisation default sharing rules. Omit (``None``) to create
                with no guardrails. ACL fields cannot be set from the SDK.
        """
        body = _SkillCreateBody(
            name=name, description=description, expected_output=expected_output,
            instructions=instructions,
            toolset=dump_toolset(toolset),
            model=model,
            connection_set=dump_json_object_list(connection_set, field_name="connection_set"),
            context_selections=dump_json_object_list(
                context_selections, field_name="context_selections"
            ),
            interfaces=dump_json_object_list(interfaces, field_name="interfaces"),
            access_config=access_config_body_for_create(guardrails),
        ).model_dump(by_alias=True, exclude_none=True)
        raw = with_retry(
            lambda: self._http.post("/api/v1/skills", json=body),
            self._config.max_retries,
        )
        return _translate_skill(_SkillWire.model_validate(raw))

    def update(
        self,
        skill_id: Union[int, str],
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
        """Update a Modus skill's configuration.

        Only the fields you pass are changed. To clear a field, name it in
        ``update_mask`` (a comma-separated list of field names) and leave its
        argument unset — the server sets each masked field to null and leaves
        fields not named in the mask untouched.

        Args:
            guardrails: Runtime guardrail labels to set on the skill. Fetches
                the current skill first and merges these labels into its access
                configuration (an extra ``get`` request). Omit (``None``) to
                leave guardrails unchanged. Pass ``[]`` to clear all guardrails.
        """
        validate_id(skill_id, name="skill_id")
        safe_id = quote(str(skill_id), safe="")
        access_config = access_config_body_for_update(
            guardrails,
            lambda: with_retry(
                lambda: self._http.get(f"/api/v1/skills/{safe_id}"),
                self._config.max_retries,
            ),
        )
        body = _SkillUpdateBody(
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
        path = _with_update_mask(f"/api/v1/skills/{safe_id}", update_mask)
        raw = with_retry(
            lambda: self._http.patch(path, json=body),
            self._config.max_retries,
        )
        return _translate_skill(_SkillWire.model_validate(raw))

    def deploy(self, skill_id: Union[int, str]) -> Skill:
        """Publish the current draft of a Modus skill."""
        validate_id(skill_id, name="skill_id")
        safe_id = quote(str(skill_id), safe="")
        raw = with_retry(
            lambda: self._http.post(f"/api/v1/skills/{safe_id}/deploy"),
            self._config.max_retries,
        )
        skill_data = raw.get("skill", raw) if isinstance(raw, dict) else raw
        return _translate_skill(_SkillWire.model_validate(skill_data))

    def delete(self, skill_id: Union[int, str]) -> None:
        """Delete a Modus skill."""
        validate_id(skill_id, name="skill_id")
        safe_id = quote(str(skill_id), safe="")
        with_retry(
            lambda: self._http.delete(f"/api/v1/skills/{safe_id}"),
            self._config.max_retries,
        )

    def request_ownership_transfer(
        self, skill_id: Union[int, str], *, new_owner_user_id: str,
    ) -> Skill:
        """Start transferring ownership of a skill to another organisation member."""
        validate_id(skill_id, name="skill_id")
        safe_id = quote(str(skill_id), safe="")
        raw = with_retry(
            lambda: self._http.post(
                f"/api/v1/skills/{safe_id}/transfer-ownership",
                json={"newOwnerUserId": new_owner_user_id},
            ),
            self._config.max_retries,
        )
        return _parse_skill_response(raw)

    def cancel_ownership_transfer(self, skill_id: Union[int, str]) -> Skill:
        """Cancel a pending skill ownership transfer."""
        validate_id(skill_id, name="skill_id")
        safe_id = quote(str(skill_id), safe="")
        raw = with_retry(
            lambda: self._http.delete(f"/api/v1/skills/{safe_id}/transfer-ownership"),
            self._config.max_retries,
        )
        return _parse_skill_response(raw)

    def accept_ownership_transfer(self, skill_id: Union[int, str]) -> Skill:
        """Accept a pending skill ownership transfer."""
        validate_id(skill_id, name="skill_id")
        safe_id = quote(str(skill_id), safe="")
        raw = with_retry(
            lambda: self._http.post(f"/api/v1/skills/{safe_id}/transfer-ownership/accept"),
            self._config.max_retries,
        )
        return _parse_skill_response(raw)

    def undelete(self, skill_id: Union[int, str]) -> Skill:
        """Restore a soft-deleted skill."""
        validate_id(skill_id, name="skill_id")
        safe_id = quote(str(skill_id), safe="")
        raw = with_retry(
            lambda: self._http.post(f"/api/v1/skills/{safe_id}/undelete"),
            self._config.max_retries,
        )
        return _parse_skill_response(raw)

    def patch_mcp_config(
        self, skill_id: Union[int, str], *, mcp_config: Dict[str, Any],
    ) -> None:
        """Update MCP server configuration for a skill."""
        validate_id(skill_id, name="skill_id")
        safe_id = quote(str(skill_id), safe="")
        with_retry(
            lambda: self._http.patch(
                f"/api/v1/skills/{safe_id}/mcp-config",
                json={"config": mcp_config},
            ),
            self._config.max_retries,
        )

    def get_variation(
        self, skill_id: Union[int, str], *, variation_uid: str,
    ) -> Skill:
        """Retrieve a historic version snapshot of a skill."""
        validate_id(skill_id, name="skill_id")
        validate_id(variation_uid, name="variation_uid")
        safe_id = quote(str(skill_id), safe="")
        safe_uid = quote(variation_uid, safe="")
        raw = with_retry(
            lambda: self._http.get(f"/api/v1/skills/{safe_id}/variations/{safe_uid}"),
            self._config.max_retries,
        )
        return _translate_skill(_SkillWire.model_validate(raw))


class AsyncSkillsResource:
    def __init__(self, http: AsyncHttpClient, config: ModusConfig) -> None:
        self._http = http
        self._config = config

    def conversations(self, skill_id: Union[int, str]) -> AsyncConversationsResource:
        """Return the conversations sub-resource scoped to ``skill_id``."""
        return AsyncConversationsResource(self._http, self._config, skill_id)

    def memories(self, skill_id: Union[int, str]) -> AsyncMemoriesResource:
        return AsyncMemoriesResource(self._http, self._config, skill_id)

    async def list(
        self,
        *,
        page_size: int = 25,
        page_token: Optional[str] = None,
        search: Optional[str] = None,
        view: Optional[VariationView] = None,
        manager_id: Optional[int] = None,
    ) -> AsyncPage[Skill]:
        """
        List all Modus skills in the organisation.

        Args:
            page_size:   Maximum number of items to return (default 25).
            page_token:  Token from a previous page's ``next_page_token``; omit for the first page.
            search:      Case-insensitive substring filter on the skill name.
            view:        Variation view — ``"active"`` (deployed) or ``"draft"``.
            manager_id:  Return only skills supervised by this manager skill id.
        """
        validate_page_size(page_size)
        return await self._list_page(page_size, page_token, search, view, manager_id)

    async def _list_page(
        self,
        page_size: int,
        page_token: Optional[str],
        search: Optional[str] = None,
        view: Optional[VariationView] = None,
        manager_id: Optional[int] = None,
    ) -> AsyncPage[Skill]:
        params = _skills_list_params(page_size, page_token, search, view, manager_id)
        data = await async_with_retry(
            lambda: self._http.get("/api/v1/skills", params=params),
            self._config.max_retries,
        )
        return build_async_aip_page_mapped(
            data,
            "skills",
            _map_skill,
            lambda cur: self._list_page(page_size, cur, search, view, manager_id),
        )

    async def get(
        self,
        skill_id: Union[int, str],
        *,
        view: Optional[VariationView] = None,
    ) -> Skill:
        """Retrieve a Modus skill with full configuration (instructions, model, and related fields)."""
        validate_id(skill_id, name="skill_id")
        safe_id = quote(str(skill_id), safe="")
        params = {} if view is None else {"view": view}
        data = await async_with_retry(
            lambda: self._http.get(f"/api/v1/skills/{safe_id}", params=params or None),
            self._config.max_retries,
        )
        return _translate_skill(_SkillWire.model_validate(data))

    async def create(
        self, name: str, *,
        description: Optional[str] = None, expected_output: Optional[str] = None,
        instructions: Optional[List[str]] = None,
        toolset: Optional[ToolsetInput] = None,
        model: Optional[str] = None,
        connection_set: Optional[JsonObjectListInput] = None,
        context_selections: Optional[JsonObjectListInput] = None,
        interfaces: Optional[JsonObjectListInput] = None,
        guardrails: Optional[List[str]] = None,
    ) -> Skill:
        """Create a new Modus skill in the organisation.

        Args:
            guardrails: Runtime guardrail labels (for example ``\"no-pii\"``).
                When set, the skill is created with these labels under the
                organisation default sharing rules. Omit (``None``) to create
                with no guardrails. ACL fields cannot be set from the SDK.
        """
        body = _SkillCreateBody(
            name=name, description=description, expected_output=expected_output,
            instructions=instructions,
            toolset=dump_toolset(toolset),
            model=model,
            connection_set=dump_json_object_list(connection_set, field_name="connection_set"),
            context_selections=dump_json_object_list(
                context_selections, field_name="context_selections"
            ),
            interfaces=dump_json_object_list(interfaces, field_name="interfaces"),
            access_config=access_config_body_for_create(guardrails),
        ).model_dump(by_alias=True, exclude_none=True)
        raw = await async_with_retry(
            lambda: self._http.post("/api/v1/skills", json=body),
            self._config.max_retries,
        )
        return _translate_skill(_SkillWire.model_validate(raw))

    async def update(
        self, skill_id: Union[int, str], *,
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
        """Update a Modus skill's configuration.

        Only the fields you pass are changed. To clear a field, name it in
        ``update_mask`` (a comma-separated list of field names) and leave its
        argument unset — the server sets each masked field to null and leaves
        fields not named in the mask untouched.

        Args:
            guardrails: Runtime guardrail labels to set on the skill. Fetches
                the current skill first and merges these labels into its access
                configuration (an extra ``get`` request). Omit (``None``) to
                leave guardrails unchanged. Pass ``[]`` to clear all guardrails.
        """
        validate_id(skill_id, name="skill_id")
        safe_id = quote(str(skill_id), safe="")
        if guardrails is not None:
            existing = await async_with_retry(
                lambda: self._http.get(f"/api/v1/skills/{safe_id}"),
                self._config.max_retries,
            )
            access_config = access_config_body_for_update(guardrails, lambda: existing)
        else:
            access_config = None
        body = _SkillUpdateBody(
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
        path = _with_update_mask(f"/api/v1/skills/{safe_id}", update_mask)
        raw = await async_with_retry(
            lambda: self._http.patch(path, json=body),
            self._config.max_retries,
        )
        return _translate_skill(_SkillWire.model_validate(raw))

    async def deploy(self, skill_id: Union[int, str]) -> Skill:
        validate_id(skill_id, name="skill_id")
        safe_id = quote(str(skill_id), safe="")
        raw = await async_with_retry(
            lambda: self._http.post(f"/api/v1/skills/{safe_id}/deploy"),
            self._config.max_retries,
        )
        skill_data = raw.get("skill", raw) if isinstance(raw, dict) else raw
        return _translate_skill(_SkillWire.model_validate(skill_data))

    async def delete(self, skill_id: Union[int, str]) -> None:
        validate_id(skill_id, name="skill_id")
        safe_id = quote(str(skill_id), safe="")
        await async_with_retry(
            lambda: self._http.delete(f"/api/v1/skills/{safe_id}"),
            self._config.max_retries,
        )

    async def request_ownership_transfer(
        self, skill_id: Union[int, str], *, new_owner_user_id: str,
    ) -> Skill:
        """Start transferring ownership of a skill to another organisation member."""
        validate_id(skill_id, name="skill_id")
        safe_id = quote(str(skill_id), safe="")
        raw = await async_with_retry(
            lambda: self._http.post(
                f"/api/v1/skills/{safe_id}/transfer-ownership",
                json={"newOwnerUserId": new_owner_user_id},
            ),
            self._config.max_retries,
        )
        return _parse_skill_response(raw)

    async def cancel_ownership_transfer(self, skill_id: Union[int, str]) -> Skill:
        """Cancel a pending skill ownership transfer."""
        validate_id(skill_id, name="skill_id")
        safe_id = quote(str(skill_id), safe="")
        raw = await async_with_retry(
            lambda: self._http.delete(f"/api/v1/skills/{safe_id}/transfer-ownership"),
            self._config.max_retries,
        )
        return _parse_skill_response(raw)

    async def accept_ownership_transfer(self, skill_id: Union[int, str]) -> Skill:
        """Accept a pending skill ownership transfer."""
        validate_id(skill_id, name="skill_id")
        safe_id = quote(str(skill_id), safe="")
        raw = await async_with_retry(
            lambda: self._http.post(f"/api/v1/skills/{safe_id}/transfer-ownership/accept"),
            self._config.max_retries,
        )
        return _parse_skill_response(raw)

    async def undelete(self, skill_id: Union[int, str]) -> Skill:
        """Restore a soft-deleted skill."""
        validate_id(skill_id, name="skill_id")
        safe_id = quote(str(skill_id), safe="")
        raw = await async_with_retry(
            lambda: self._http.post(f"/api/v1/skills/{safe_id}/undelete"),
            self._config.max_retries,
        )
        return _parse_skill_response(raw)

    async def patch_mcp_config(
        self, skill_id: Union[int, str], *, mcp_config: Dict[str, Any],
    ) -> None:
        """Update MCP server configuration for a skill."""
        validate_id(skill_id, name="skill_id")
        safe_id = quote(str(skill_id), safe="")
        await async_with_retry(
            lambda: self._http.patch(
                f"/api/v1/skills/{safe_id}/mcp-config",
                json={"config": mcp_config},
            ),
            self._config.max_retries,
        )

    async def get_variation(
        self, skill_id: Union[int, str], *, variation_uid: str,
    ) -> Skill:
        """Retrieve a historic version snapshot of a skill."""
        validate_id(skill_id, name="skill_id")
        validate_id(variation_uid, name="variation_uid")
        safe_id = quote(str(skill_id), safe="")
        safe_uid = quote(variation_uid, safe="")
        raw = await async_with_retry(
            lambda: self._http.get(f"/api/v1/skills/{safe_id}/variations/{safe_uid}"),
            self._config.max_retries,
        )
        return _translate_skill(_SkillWire.model_validate(raw))
