"""Skills resource — /api/v1/skills (full CRUD, management SDK)"""

from __future__ import annotations
from typing import Any, Dict, List, Optional, Union
from urllib.parse import quote

from modus._config import ModusConfig
from modus._http import AsyncHttpClient, HttpClient
from modus._retry import async_with_retry, with_retry
from modus._pagination import aip_list_params, build_aip_page_mapped, build_async_aip_page_mapped
from modus._validation import validate_id, validate_page_size
from ..._wire.skills import _SkillWire
from modus.types.pagination import AsyncPage, Page
from ...types.skills import Skill
from .conversations import AsyncConversationsResource, ConversationsResource
from ._translate import _translate_skill
from ._update_body import _SkillCreateBody, _SkillUpdateBody


def _map_skill(raw: dict) -> Skill:
    return _translate_skill(_SkillWire.model_validate(raw))


class SkillsResource:
    """
    Full CRUD access to Modus skills.

    mgmt.skills.list()                              → Page[Skill]
    mgmt.skills.get(skill_id)                       → Skill (with variation fields)
    mgmt.skills.create(name, *, ...)                → Skill
    mgmt.skills.update(skill_id, *, ...)            → Skill
    mgmt.skills.deploy(skill_id)                    → Skill
    mgmt.skills.delete(skill_id)                    → None
    mgmt.skills.conversations(skill_id).list(...)   → Page[ConversationListItem]
    mgmt.skills.conversations(skill_id).get(tid)    → Conversation
    """

    def __init__(self, http: HttpClient, config: ModusConfig) -> None:
        self._http = http
        self._config = config
        self._conversations = ConversationsResource(http, config)

    def conversations(self, skill_id: Union[int, str]) -> ConversationsResource:
        """Return the conversations sub-resource scoped to skill_id."""
        # We wrap it to bind the skill_id — but ConversationsResource already
        # takes skill_id per-call, so just return the shared instance.
        return self._conversations

    def list(
        self,
        *,
        page_size: int = 25,
        page_token: Optional[str] = None,
    ) -> Page[Skill]:
        validate_page_size(page_size)
        return self._list_page(page_size, page_token)

    def _list_page(self, page_size: int, page_token: Optional[str]) -> Page[Skill]:
        params = aip_list_params(page_size, page_token)
        data = with_retry(
            lambda: self._http.get("/api/v1/skills", params=params),
            self._config.max_retries,
        )
        return build_aip_page_mapped(
            data,
            "skills",
            _map_skill,
            lambda cur: self._list_page(page_size, cur),
        )

    def get(self, skill_id: Union[int, str]) -> Skill:
        """Retrieve a skill with full variation detail (instructions, model, etc.)."""
        validate_id(skill_id, name="skill_id")
        safe_id = quote(str(skill_id), safe="")
        data = with_retry(
            lambda: self._http.get(f"/api/v1/skills/{safe_id}"),
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
        toolset: Optional[Dict[str, Any]] = None,
        model: Optional[str] = None,
        connection_set: Optional[List[Dict[str, Any]]] = None,
        context_selections: Optional[List[Dict[str, Any]]] = None,
        interfaces: Optional[List[Dict[str, Any]]] = None,
        access_config: Optional[Dict[str, Any]] = None,
    ) -> Skill:
        body = _SkillCreateBody(
            name=name, description=description, expected_output=expected_output,
            instructions=instructions, toolset=toolset, model=model,
            connection_set=connection_set, context_selections=context_selections,
            interfaces=interfaces, access_config=access_config,
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
        toolset: Optional[Dict[str, Any]] = None,
        model: Optional[str] = None,
        connection_set: Optional[List[Dict[str, Any]]] = None,
        context_selections: Optional[List[Dict[str, Any]]] = None,
        interfaces: Optional[List[Dict[str, Any]]] = None,
        access_config: Optional[Dict[str, Any]] = None,
        manager_id: Optional[str] = None,
    ) -> Skill:
        body = _SkillUpdateBody(
            name=name, description=description, expected_output=expected_output,
            instructions=instructions, toolset=toolset, model=model,
            connection_set=connection_set, context_selections=context_selections,
            interfaces=interfaces, access_config=access_config, manager_id=manager_id,
        ).model_dump(by_alias=True, exclude_none=True)
        validate_id(skill_id, name="skill_id")
        safe_id = quote(str(skill_id), safe="")
        raw = with_retry(
            lambda: self._http.patch(f"/api/v1/skills/{safe_id}", json=body),
            self._config.max_retries,
        )
        return _translate_skill(_SkillWire.model_validate(raw))

    def deploy(self, skill_id: Union[int, str]) -> Skill:
        validate_id(skill_id, name="skill_id")
        safe_id = quote(str(skill_id), safe="")
        raw = with_retry(
            lambda: self._http.post(f"/api/v1/skills/{safe_id}/deploy"),
            self._config.max_retries,
        )
        skill_data = raw.get("skill", raw) if isinstance(raw, dict) else raw
        return _translate_skill(_SkillWire.model_validate(skill_data))

    def delete(self, skill_id: Union[int, str]) -> None:
        validate_id(skill_id, name="skill_id")
        safe_id = quote(str(skill_id), safe="")
        with_retry(
            lambda: self._http.delete(f"/api/v1/skills/{safe_id}"),
            self._config.max_retries,
        )


class AsyncSkillsResource:
    def __init__(self, http: AsyncHttpClient, config: ModusConfig) -> None:
        self._http = http
        self._config = config
        self._conversations = AsyncConversationsResource(http, config)

    def conversations(self, skill_id: Union[int, str]) -> AsyncConversationsResource:
        return self._conversations

    async def list(
        self,
        *,
        page_size: int = 25,
        page_token: Optional[str] = None,
    ) -> AsyncPage[Skill]:
        validate_page_size(page_size)
        return await self._list_page(page_size, page_token)

    async def _list_page(
        self, page_size: int, page_token: Optional[str]
    ) -> AsyncPage[Skill]:
        params = aip_list_params(page_size, page_token)
        data = await async_with_retry(
            lambda: self._http.get("/api/v1/skills", params=params),
            self._config.max_retries,
        )
        return build_async_aip_page_mapped(
            data,
            "skills",
            _map_skill,
            lambda cur: self._list_page(page_size, cur),
        )

    async def get(self, skill_id: Union[int, str]) -> Skill:
        validate_id(skill_id, name="skill_id")
        safe_id = quote(str(skill_id), safe="")
        data = await async_with_retry(
            lambda: self._http.get(f"/api/v1/skills/{safe_id}"),
            self._config.max_retries,
        )
        return _translate_skill(_SkillWire.model_validate(data))

    async def create(
        self, name: str, *,
        description: Optional[str] = None, expected_output: Optional[str] = None,
        instructions: Optional[List[str]] = None, toolset: Optional[Dict[str, Any]] = None,
        model: Optional[str] = None, connection_set: Optional[List[Dict[str, Any]]] = None,
        context_selections: Optional[List[Dict[str, Any]]] = None,
        interfaces: Optional[List[Dict[str, Any]]] = None,
        access_config: Optional[Dict[str, Any]] = None,
    ) -> Skill:
        body = _SkillCreateBody(
            name=name, description=description, expected_output=expected_output,
            instructions=instructions, toolset=toolset, model=model,
            connection_set=connection_set, context_selections=context_selections,
            interfaces=interfaces, access_config=access_config,
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
        toolset: Optional[Dict[str, Any]] = None, model: Optional[str] = None,
        connection_set: Optional[List[Dict[str, Any]]] = None,
        context_selections: Optional[List[Dict[str, Any]]] = None,
        interfaces: Optional[List[Dict[str, Any]]] = None,
        access_config: Optional[Dict[str, Any]] = None,
        manager_id: Optional[str] = None,
    ) -> Skill:
        body = _SkillUpdateBody(
            name=name, description=description, expected_output=expected_output,
            instructions=instructions, toolset=toolset, model=model,
            connection_set=connection_set, context_selections=context_selections,
            interfaces=interfaces, access_config=access_config, manager_id=manager_id,
        ).model_dump(by_alias=True, exclude_none=True)
        validate_id(skill_id, name="skill_id")
        safe_id = quote(str(skill_id), safe="")
        raw = await async_with_retry(
            lambda: self._http.patch(f"/api/v1/skills/{safe_id}", json=body),
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
