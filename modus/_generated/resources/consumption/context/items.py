# Auto-generated from the Modus API schema. Do not edit by hand.

from __future__ import annotations

from modus._config import ModusConfig
from modus._http import AsyncHttpClient, HttpClient
from modus._openapi_invoke import invoke_operation, invoke_operation_async
from modus._retry import async_with_retry, with_retry
from modus.types.context import ContextItemsQuery, ContextItemsQueryResult


class _ContextItemsResourceBase:
    """Generated base for the consumption ``context.items`` resource."""

    def __init__(self, http: HttpClient, config: ModusConfig) -> None:
        self._http = http
        self._config = config

    def query(self, query: ContextItemsQuery) -> ContextItemsQueryResult:
        """
        Query context items with SQL.

        Runs one read-only SQL statement over the ``context_items`` table and returns its rows. The
        query sees only the items you can read. A query that is not read-only or not valid returns
        400; one that runs past 20 s returns 422.

        **Requires:** ``context:read``

        Args:
            query: Request body; see :class:`ContextItemsQuery`.

        Example:
            >>> result = modus.context.items.query(ContextItemsQuery(sql="SELECT context_type, count(*) AS items FROM context_items GROUP BY context_type"))
            >>> result.rows
        """
        body = query.model_dump(by_alias=True, exclude_none=True)
        raw = with_retry(
            lambda: invoke_operation(
                self._http,
                "ContextItemsQueryController_query",
                json_body=body,
            ),
            self._config.max_retries,
        )
        return ContextItemsQueryResult.model_validate(raw)


class _AsyncContextItemsResourceBase:
    """Generated base for the consumption ``context.items`` resource."""

    def __init__(self, http: AsyncHttpClient, config: ModusConfig) -> None:
        self._http = http
        self._config = config

    async def query(self, query: ContextItemsQuery) -> ContextItemsQueryResult:
        """
        Query context items with SQL.

        Runs one read-only SQL statement over the ``context_items`` table and returns its rows. The
        query sees only the items you can read. A query that is not read-only or not valid returns
        400; one that runs past 20 s returns 422.

        **Requires:** ``context:read``

        Args:
            query: Request body; see :class:`ContextItemsQuery`.
        """
        body = query.model_dump(by_alias=True, exclude_none=True)
        raw = await async_with_retry(
            lambda: invoke_operation_async(
                self._http,
                "ContextItemsQueryController_query",
                json_body=body,
            ),
            self._config.max_retries,
        )
        return ContextItemsQueryResult.model_validate(raw)
