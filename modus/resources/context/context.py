"""Context resource — read-only access to the knowledge base (consumption SDK)."""

from __future__ import annotations

from ..._config import ModusConfig
from ..._http import AsyncHttpClient, HttpClient
from .items import AsyncContextItemsResource, ContextItemsResource


class ContextResource:
    """
    Read access to the Modus knowledge base.

    client.context.items.list() → Page[ContextItem]
    client.context.items.get(uid) → ContextItem

    To create or update context items use modus.management.ModusManagement.
    """

    def __init__(self, http: HttpClient, config: ModusConfig) -> None:
        self._http = http
        self._config = config
        self.items = ContextItemsResource(http, config)


class AsyncContextResource:
    """
    Async read access to the Modus knowledge base.

    await client.context.items.list() → AsyncPage[ContextItem]
    await client.context.items.get(uid) → ContextItem

    To create or update context items use modus.management.ModusManagement.
    """

    def __init__(self, http: AsyncHttpClient, config: ModusConfig) -> None:
        self._http = http
        self._config = config
        self.items = AsyncContextItemsResource(http, config)
