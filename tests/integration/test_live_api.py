"""
Live modus-api smoke tests (optional).

Run only when a PAT and local (or staging) API are available:

    set -a && source ../../../../.env && set +a
    cd distribution/clients/python/modus-sdk
    uv run pytest tests/integration/ -m integration -v

Skipped in default CI (no running stack / secrets).
"""
from __future__ import annotations

import os

import pytest
from modus import Modus

pytestmark = pytest.mark.integration

_has_live = bool(os.getenv("MODUS_API_KEY"))


@pytest.mark.skipif(not _has_live, reason="MODUS_API_KEY not set")
def test_skills_list_aip_pagination() -> None:
    page = Modus().scopes.list(page_size=2)
    assert isinstance(page.items, list)


@pytest.mark.skipif(not _has_live, reason="MODUS_API_KEY not set")
def test_context_items_list_single_context_type() -> None:
    """Requires modus-api ListContextItemsQueryDto @Transform (restart after deploy)."""
    page = Modus().context.items.list(context_type="note", page_size=1)
    assert isinstance(page.items, list)
