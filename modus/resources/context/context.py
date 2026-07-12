"""Context resource — read-only access to the knowledge base (consumption SDK)."""

from __future__ import annotations

from modus.management.resources.context.custom_items import (
    AsyncCustomContextItemsResource,
    CustomContextItemsResource,
)

from ..._config import ModusConfig
from ..._http import AsyncHttpClient, HttpClient
from .items import AsyncContextItemsResource, ContextItemsResource


class ContextResource:
    """
    Read access to the Modus knowledge base.

    client.context.items.list() → Page[ContextItem]
    client.context.items.get(uid) → ContextItem
    client.context.custom_items.list() → Page[ContextItem]

    To create or update context items use modus.management.ModusManagement.
    """

    def __init__(self, http: HttpClient, config: ModusConfig) -> None:
        self._http = http
        self._config = config
        self.items = ContextItemsResource(http, config)
        self.custom_items = CustomContextItemsResource(http, config)


class AsyncContextResource:
    """
    Async read access to the Modus knowledge base.

    await client.context.items.list() → AsyncPage[ContextItem]
    await client.context.items.get(uid) → ContextItem
    await client.context.custom_items.list() → AsyncPage[ContextItem]

    To create or update context items use modus.management.ModusManagement.
    """

    def __init__(self, http: AsyncHttpClient, config: ModusConfig) -> None:
        self._http = http
        self._config = config
        self.items = AsyncContextItemsResource(http, config)
        self.custom_items = AsyncCustomContextItemsResource(http, config)
