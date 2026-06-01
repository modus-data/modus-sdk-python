"""
Pagination types for list endpoints.

``Page`` and ``AsyncPage`` hold one page of results. Iterating a page yields
only that page's items; use ``auto_paging_iter()`` to walk all pages, or
``get_next_page()`` for manual control. See the package README for examples.
"""

from __future__ import annotations
from typing import AsyncIterator, Awaitable, Callable, Generic, Iterator, List, Optional, TypeVar

T = TypeVar("T")


class Page(Generic[T]):
    """A single page of results from a Modus list endpoint (sync)."""

    def __init__(
        self,
        items: List[T],
        next_page_token: Optional[str],
        _fetch_page: Callable[[str], "Page[T]"],
    ) -> None:
        self.items = items
        self.next_page_token = next_page_token
        self._fetch_page = _fetch_page

    def has_next_page(self) -> bool:
        """Return True if more pages are available."""
        return self.next_page_token is not None

    def get_next_page(self) -> "Page[T]":
        """Fetch and return the next page. Raises ValueError if no next page."""
        if self.next_page_token is None:
            raise ValueError(
                "No next page available. Check has_next_page() before calling get_next_page()."
            )
        return self._fetch_page(self.next_page_token)

    def auto_paging_iter(self) -> Iterator[T]:
        """
        Iterate over all items across all pages, fetching lazily as needed.

        Warning: may make multiple API calls for large result sets.
        """
        page: Page[T] = self
        while True:
            yield from page.items
            if not page.has_next_page():
                break
            page = page.get_next_page()

    def __iter__(self) -> Iterator[T]:
        """Iterate over the current page's items only."""
        return iter(self.items)

    def __len__(self) -> int:
        return len(self.items)

    def __repr__(self) -> str:
        return f"Page(count={len(self.items)}, has_next_page={self.has_next_page()})"


class AsyncPage(Generic[T]):
    """A single page of results from a Modus list endpoint (async)."""

    def __init__(
        self,
        items: List[T],
        next_page_token: Optional[str],
        _fetch_page: Callable[[str], Awaitable[AsyncPage[T]]],
    ) -> None:
        self.items = items
        self.next_page_token = next_page_token
        self._fetch_page = _fetch_page

    def has_next_page(self) -> bool:
        """Return True if more pages are available."""
        return self.next_page_token is not None

    async def get_next_page(self) -> "AsyncPage[T]":
        """Fetch and return the next page. Raises ValueError if no next page."""
        if self.next_page_token is None:
            raise ValueError(
                "No next page available. Check has_next_page() before calling get_next_page()."
            )
        return await self._fetch_page(self.next_page_token)

    async def auto_paging_iter(self) -> AsyncIterator[T]:
        """
        Async-iterate over all items across all pages, fetching lazily as needed.

        Usage:
            async for item in page.auto_paging_iter():
                process(item)
        """
        page: AsyncPage[T] = self
        while True:
            for item in page.items:
                yield item
            if not page.has_next_page():
                break
            page = await page.get_next_page()

    def __iter__(self) -> Iterator[T]:
        """Iterate over the current page's items only (sync, no network calls)."""
        return iter(self.items)

    def __len__(self) -> int:
        return len(self.items)

    def __repr__(self) -> str:
        return f"AsyncPage(count={len(self.items)}, has_next_page={self.has_next_page()})"
