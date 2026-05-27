import pytest
from modus._pagination import build_page
from modus._exceptions import ModusError
from modus.types.skills import Skill


def test_build_page_raises_on_missing_items_key():
    with pytest.raises(ModusError, match="missing 'items'"):
        build_page({"error": "unexpected"}, Skill, lambda _: None)


def test_build_page_raises_on_non_dict():
    with pytest.raises(ModusError, match="missing 'items'"):
        build_page([], Skill, lambda _: None)


def test_build_page_ok_with_empty_items():
    page = build_page({"items": [], "nextCursor": None}, Skill, lambda _: None)
    assert len(page) == 0
