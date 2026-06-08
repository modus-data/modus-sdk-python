"""Context resource — knowledge base management (modus.management)."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from modus._config import ModusConfig
from modus._http import AsyncHttpClient, HttpClient
from modus._retry import async_with_retry, with_retry

from ...types.context import CreatedContextItem
from .items import AsyncContextItemsResource, ContextItemsResource


class ContextResource:
    """
    Full knowledge base access for modus.management.ModusManagement.

    mgmt.context.items.list()               → Page[ContextItem]
    mgmt.context.items.get(uid)             → ContextItem
    mgmt.context.items.update(uid, ...)     → ContextItem
    mgmt.context.items.delete(uid)          → ContextItemDeletion
    mgmt.context.create_note(title, content)              → CreatedContextItem
    mgmt.context.create_saved_query(name, query, ...)     → CreatedContextItem
    mgmt.context.create_link(url, ...)                    → CreatedContextItem
    """

    def __init__(self, http: HttpClient, config: ModusConfig) -> None:
        self._http = http
        self._config = config
        self.items = ContextItemsResource(http, config)

    def _create(self, endpoint: str, payload: Dict[str, Any]) -> CreatedContextItem:
        data = with_retry(
            lambda: self._http.post(endpoint, json=payload),
            self._config.max_retries,
        )
        return CreatedContextItem.model_validate(data)

    def create_note(self, title: str, content: str) -> CreatedContextItem:
        """Add a free-form text note to the Modus knowledge base."""
        return self._create("/api/v1/context/notes", {"title": title, "content": content})

    def create_saved_query(
        self, name: str, query: Optional[str] = None, *, connection_id: str,
        description: Optional[str] = None, path: Optional[List[str]] = None,
    ) -> CreatedContextItem:
        """Save a SQL query to the Modus knowledge base."""
        payload: Dict[str, Any] = {"name": name, "connectionId": connection_id}
        if query is not None:
            payload["query"] = query
        if description is not None:
            payload["description"] = description
        if path is not None:
            payload["path"] = path
        return self._create("/api/v1/context/saved-queries", payload)

    def create_link(
        self, url: str, *, title: Optional[str] = None,
        is_crawl: Optional[bool] = None, page_limit: Optional[int] = None,
    ) -> CreatedContextItem:
        """Add a URL to the Modus knowledge base."""
        payload: Dict[str, Any] = {"url": url}
        if title is not None:
            payload["title"] = title
        if is_crawl is not None:
            payload["isCrawl"] = is_crawl
        if page_limit is not None:
            payload["pageLimit"] = page_limit
        return self._create("/api/v1/context/links", payload)

    def create_dimension(
        self,
        name: str,
        *,
        expr: str,
        description: Optional[str] = None,
        data_type: str = "TEXT",
    ) -> CreatedContextItem:
        """Add a semantic dimension to the Modus knowledge base."""
        payload: Dict[str, Any] = {
            "name": name,
            "expr": expr,
            "description": description if description is not None else "",
            "dataType": data_type,
        }
        return self._create("/api/v1/context/dimensions", payload)

    def create_fact(
        self,
        name: str,
        *,
        expr: str,
        description: Optional[str] = None,
        aggregation: str = "SUM",
        data_type: str = "NUMBER",
    ) -> CreatedContextItem:
        """Add a semantic fact to the Modus knowledge base."""
        payload: Dict[str, Any] = {
            "name": name,
            "expr": expr,
            "description": description if description is not None else "",
            "aggregation": aggregation,
            "dataType": data_type,
        }
        return self._create("/api/v1/context/facts", payload)

    def create_metric(
        self,
        name: str,
        *,
        expr: str,
        description: Optional[str] = None,
    ) -> CreatedContextItem:
        """Add a semantic metric to the Modus knowledge base."""
        payload: Dict[str, Any] = {
            "name": name,
            "expr": expr,
            "description": description if description is not None else "",
        }
        return self._create("/api/v1/context/metrics", payload)

    def create_filter(
        self,
        name: str,
        *,
        expr: str,
        description: Optional[str] = None,
    ) -> CreatedContextItem:
        """Add a semantic filter to the Modus knowledge base."""
        payload: Dict[str, Any] = {
            "name": name,
            "expr": expr,
            "description": description if description is not None else "",
        }
        return self._create("/api/v1/context/filters", payload)


class AsyncContextResource:
    def __init__(self, http: AsyncHttpClient, config: ModusConfig) -> None:
        self._http = http
        self._config = config
        self.items = AsyncContextItemsResource(http, config)

    async def _create(self, endpoint: str, payload: Dict[str, Any]) -> CreatedContextItem:
        data = await async_with_retry(
            lambda: self._http.post(endpoint, json=payload),
            self._config.max_retries,
        )
        return CreatedContextItem.model_validate(data)

    async def create_note(self, title: str, content: str) -> CreatedContextItem:
        return await self._create("/api/v1/context/notes", {"title": title, "content": content})

    async def create_saved_query(
        self, name: str, query: Optional[str] = None, *, connection_id: str,
        description: Optional[str] = None, path: Optional[List[str]] = None,
    ) -> CreatedContextItem:
        payload: Dict[str, Any] = {"name": name, "connectionId": connection_id}
        if query is not None:
            payload["query"] = query
        if description is not None:
            payload["description"] = description
        if path is not None:
            payload["path"] = path
        return await self._create("/api/v1/context/saved-queries", payload)

    async def create_link(
        self, url: str, *, title: Optional[str] = None,
        is_crawl: Optional[bool] = None, page_limit: Optional[int] = None,
    ) -> CreatedContextItem:
        payload: Dict[str, Any] = {"url": url}
        if title is not None:
            payload["title"] = title
        if is_crawl is not None:
            payload["isCrawl"] = is_crawl
        if page_limit is not None:
            payload["pageLimit"] = page_limit
        return await self._create("/api/v1/context/links", payload)

    async def create_dimension(
        self,
        name: str,
        *,
        expr: str,
        description: Optional[str] = None,
        data_type: str = "TEXT",
    ) -> CreatedContextItem:
        """Add a semantic dimension to the Modus knowledge base."""
        payload: Dict[str, Any] = {
            "name": name,
            "expr": expr,
            "description": description if description is not None else "",
            "dataType": data_type,
        }
        return await self._create("/api/v1/context/dimensions", payload)

    async def create_fact(
        self,
        name: str,
        *,
        expr: str,
        description: Optional[str] = None,
        aggregation: str = "SUM",
        data_type: str = "NUMBER",
    ) -> CreatedContextItem:
        """Add a semantic fact to the Modus knowledge base."""
        payload: Dict[str, Any] = {
            "name": name,
            "expr": expr,
            "description": description if description is not None else "",
            "aggregation": aggregation,
            "dataType": data_type,
        }
        return await self._create("/api/v1/context/facts", payload)

    async def create_metric(
        self,
        name: str,
        *,
        expr: str,
        description: Optional[str] = None,
    ) -> CreatedContextItem:
        """Add a semantic metric to the Modus knowledge base."""
        payload: Dict[str, Any] = {
            "name": name,
            "expr": expr,
            "description": description if description is not None else "",
        }
        return await self._create("/api/v1/context/metrics", payload)

    async def create_filter(
        self,
        name: str,
        *,
        expr: str,
        description: Optional[str] = None,
    ) -> CreatedContextItem:
        """Add a semantic filter to the Modus knowledge base."""
        payload: Dict[str, Any] = {
            "name": name,
            "expr": expr,
            "description": description if description is not None else "",
        }
        return await self._create("/api/v1/context/filters", payload)
