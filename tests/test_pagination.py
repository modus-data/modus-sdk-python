"""Tests for Page[T], AsyncPage[T], and pagination helpers."""

import pytest
from modus.types.pagination import AsyncPage, Page


def _make_page(items, next_page_token=None, pages=None):
    """Helper: create a Page with a fetch function cycling through `pages`."""
    call_count = {"n": 0}

    def fetch(cursor):
        idx = call_count["n"]
        call_count["n"] += 1
        if pages and idx < len(pages):
            new_items, new_cursor = pages[idx]
            return _make_page(new_items, new_cursor, pages[idx + 1:] if idx + 1 < len(pages) else None)
        raise ValueError("Unexpected page fetch")

    return Page(items=items, next_page_token=next_page_token, _fetch_page=fetch)


def test_iterate_current_page_only():
    page = _make_page([1, 2, 3])
    assert list(page) == [1, 2, 3]


def test_has_next_page_true():
    page = _make_page([1], next_page_token="cur_abc")
    assert page.has_next_page() is True


def test_has_next_page_false():
    page = _make_page([1], next_page_token=None)
    assert page.has_next_page() is False


def test_get_next_page():
    next_page = _make_page([4, 5])
    page = Page(items=[1, 2, 3], next_page_token="cur", _fetch_page=lambda _: next_page)
    result = page.get_next_page()
    assert list(result) == [4, 5]


def test_get_next_page_raises_when_no_next():
    page = _make_page([1], next_page_token=None)
    with pytest.raises(ValueError, match="No next page"):
        page.get_next_page()


def test_auto_paging_iter_single_page():
    page = _make_page([1, 2, 3])
    assert list(page.auto_paging_iter()) == [1, 2, 3]


def test_auto_paging_iter_two_pages():
    page2 = _make_page([3, 4], next_page_token=None)
    page1 = Page(items=[1, 2], next_page_token="c1", _fetch_page=lambda _: page2)
    assert list(page1.auto_paging_iter()) == [1, 2, 3, 4]


def test_auto_paging_iter_three_pages():
    page3 = _make_page([5], next_page_token=None)
    page2 = Page(items=[3, 4], next_page_token="c2", _fetch_page=lambda _: page3)
    page1 = Page(items=[1, 2], next_page_token="c1", _fetch_page=lambda _: page2)
    assert list(page1.auto_paging_iter()) == [1, 2, 3, 4, 5]


def test_len():
    page = _make_page([1, 2, 3])
    assert len(page) == 3


def test_repr_with_next():
    page = _make_page([1, 2], next_page_token="abc")
    assert "has_next_page=True" in repr(page)
    assert "count=2" in repr(page)


def test_repr_without_next():
    page = _make_page([1])
    assert "has_next_page=False" in repr(page)


# ---------------------------------------------------------------------------
# AsyncPage tests
# ---------------------------------------------------------------------------


def _make_async_page(items, next_page_token=None, pages=None):
    """Helper: create an AsyncPage with an async fetch function."""

    async def fetch(cursor):
        if pages:
            new_items, new_cursor = pages[0]
            return _make_async_page(new_items, new_cursor, pages[1:] if len(pages) > 1 else None)
        raise ValueError("Unexpected page fetch")

    return AsyncPage(items=items, next_page_token=next_page_token, _fetch_page=fetch)


def test_async_page_iterate_current_page():
    page = _make_async_page([10, 20, 30])
    assert list(page) == [10, 20, 30]


def test_async_page_len():
    page = _make_async_page([10, 20])
    assert len(page) == 2


def test_async_page_repr():
    page = _make_async_page([1, 2], next_page_token="x")
    assert "has_next_page=True" in repr(page)
    assert "count=2" in repr(page)


def test_async_page_has_next_page():
    assert _make_async_page([1], next_page_token="c").has_next_page() is True
    assert _make_async_page([1], next_page_token=None).has_next_page() is False


@pytest.mark.asyncio
async def test_async_page_get_next_page():
    async def fetch(_cursor):
        return _make_async_page([4, 5])

    page = AsyncPage(items=[1, 2, 3], next_page_token="c", _fetch_page=fetch)
    result = await page.get_next_page()
    assert list(result) == [4, 5]


@pytest.mark.asyncio
async def test_async_page_get_next_page_raises_when_no_next():
    page = _make_async_page([1], next_page_token=None)
    with pytest.raises(ValueError, match="No next page"):
        await page.get_next_page()


@pytest.mark.asyncio
async def test_async_page_auto_paging_iter_single_page():
    page = _make_async_page([1, 2, 3])
    result = [item async for item in page.auto_paging_iter()]
    assert result == [1, 2, 3]


@pytest.mark.asyncio
async def test_async_page_auto_paging_iter_two_pages():
    page2 = _make_async_page([3, 4], next_page_token=None)

    async def fetch(_cursor):
        return page2

    page1 = AsyncPage(items=[1, 2], next_page_token="c1", _fetch_page=fetch)
    result = [item async for item in page1.auto_paging_iter()]
    assert result == [1, 2, 3, 4]


@pytest.mark.asyncio
async def test_async_page_auto_paging_iter_three_pages():
    page3 = _make_async_page([5], next_page_token=None)

    async def fetch2(_cursor):
        return page3

    page2 = AsyncPage(items=[3, 4], next_page_token="c2", _fetch_page=fetch2)

    async def fetch1(_cursor):
        return page2

    page1 = AsyncPage(items=[1, 2], next_page_token="c1", _fetch_page=fetch1)
    result = [item async for item in page1.auto_paging_iter()]
    assert result == [1, 2, 3, 4, 5]
