"""Skills resource — /api/v1/skills (read-only, consumption SDK)"""

from __future__ import annotations
from typing import Optional, Union
from urllib.parse import quote

from ..._chat import (
    AsyncChatStream,
    ChatStream,
    chat_buffered,
    chat_buffered_async,
    chat_stream_session,
    chat_stream_session_async,
)
from ..._config import ModusConfig
from ..._http import AsyncHttpClient, HttpClient
from ..._pagination import (
    aip_list_params,
    build_aip_page_mapped,
    build_async_aip_page_mapped,
)
from ..._retry import async_with_retry, with_retry
from ..._validation import validate_id, validate_page_size
from ..._wire.context_compose import (
    _ComposeSkillContextRequestWire,
    _ComposeSkillContextResponseWire,
)
from ..._wire.skills import _SkillWire
from ...types.chat import ChatResult
from ...types.context_compose import SkillContextComposition
from ...types.pagination import AsyncPage, Page
from ...types.skills import Skill
from .conversations import AsyncConversationsResource, ConversationsResource
from ._translate import _translate_skill


def _map_skill(raw: dict) -> Skill:
    return _translate_skill(_SkillWire.model_validate(raw))


class SkillsResource:
    """
    Read access to Modus skills.

    client.skills.list()                               → Page[Skill]
    client.skills.get(skill_id)                        → Skill
    client.skills.conversations.list(skill_id)         → Page[ConversationListItem]
    client.skills.conversations.get(skill_id, thread)  → Conversation

    To create, update, or deploy skills use modus.management.ModusManagement.
    """

    def __init__(self, http: HttpClient, config: ModusConfig) -> None:
        self._http = http
        self._config = config
        self.conversations = ConversationsResource(http, config)

    def list(
        self,
        *,
        page_size: int = 25,
        page_token: Optional[str] = None,
    ) -> Page[Skill]:
        """
        List skills in the organisation.

        Args:
            page_size:  Items per page (default 25, AIP-158).
            page_token: Opaque token from a previous page's ``next_page_token``.
        """
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
        """
        Retrieve a skill by ID or slug.

        Raises:
            NotFoundError: if no skill with this ID/slug exists.
        """
        validate_id(skill_id, name="skill_id")
        safe_id = quote(str(skill_id), safe="")
        data = with_retry(
            lambda: self._http.get(f"/api/v1/skills/{safe_id}"),
            self._config.max_retries,
        )
        return _translate_skill(_SkillWire.model_validate(data))

    def chat(
        self,
        skill_id: Union[int, str],
        message: str,
        *,
        model: str,
        thread_id: Optional[str] = None,
    ) -> ChatResult:
        return chat_buffered(
            self._http,
            "skills",
            skill_id,
            message,
            model=model,
            thread_id=thread_id,
        )

    def chat_stream(
        self,
        skill_id: Union[int, str],
        message: str,
        *,
        model: str,
        thread_id: Optional[str] = None,
    ) -> ChatStream:
        return chat_stream_session(
            self._http,
            "skills",
            skill_id,
            message,
            model=model,
            thread_id=thread_id,
        )

    def get_context(
        self,
        skill_id: Union[int, str],
        message: str,
        *,
        limit: Optional[int] = None,
    ) -> SkillContextComposition:
        validate_id(skill_id, name="skill_id")
        safe_id = quote(str(skill_id), safe="")
        body = _ComposeSkillContextRequestWire(message=message, limit=limit)
        data = with_retry(
            lambda: self._http.post(
                f"/api/v1/skills/{safe_id}/context",
                json=body.model_dump(by_alias=True, exclude_none=True),
            ),
            self._config.max_retries,
        )
        wire = _ComposeSkillContextResponseWire.model_validate(data)
        return SkillContextComposition.model_validate(wire.model_dump(by_alias=True))


class AsyncSkillsResource:
    """
    Async read access to Modus skills.

    await client.skills.list()                               → AsyncPage[Skill]
    await client.skills.get(skill_id)                        → Skill
    await client.skills.conversations.list(skill_id, ...)    → AsyncPage[ConversationListItem]

    To create, update, or deploy skills use modus.management.ModusManagement.
    """

    def __init__(self, http: AsyncHttpClient, config: ModusConfig) -> None:
        self._http = http
        self._config = config
        self.conversations = AsyncConversationsResource(http, config)

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

    async def chat(
        self,
        skill_id: Union[int, str],
        message: str,
        *,
        model: str,
        thread_id: Optional[str] = None,
    ) -> ChatResult:
        return await chat_buffered_async(
            self._http,
            "skills",
            skill_id,
            message,
            model=model,
            thread_id=thread_id,
        )

    def chat_stream(
        self,
        skill_id: Union[int, str],
        message: str,
        *,
        model: str,
        thread_id: Optional[str] = None,
    ) -> AsyncChatStream:
        return chat_stream_session_async(
            self._http,
            "skills",
            skill_id,
            message,
            model=model,
            thread_id=thread_id,
        )

    async def get_context(
        self,
        skill_id: Union[int, str],
        message: str,
        *,
        limit: Optional[int] = None,
    ) -> SkillContextComposition:
        validate_id(skill_id, name="skill_id")
        safe_id = quote(str(skill_id), safe="")
        body = _ComposeSkillContextRequestWire(message=message, limit=limit)
        data = await async_with_retry(
            lambda: self._http.post(
                f"/api/v1/skills/{safe_id}/context",
                json=body.model_dump(by_alias=True, exclude_none=True),
            ),
            self._config.max_retries,
        )
        wire = _ComposeSkillContextResponseWire.model_validate(data)
        return SkillContextComposition.model_validate(wire.model_dump(by_alias=True))
