import pytest
from modus._exceptions import ModusError
from modus._pagination import build_aip_page
from modus.types.skills import Skill


def test_build_aip_page_raises_on_missing_items_key():
    with pytest.raises(ModusError, match="missing 'skills'"):
        build_aip_page({"error": "unexpected"}, "skills", Skill, lambda _: None)


def test_build_aip_page_raises_on_non_dict():
    with pytest.raises(ModusError, match="missing 'skills'"):
        build_aip_page([], "skills", Skill, lambda _: None)


def test_build_aip_page_ok_with_empty_items():
    page = build_aip_page({"skills": [], "nextPageToken": None}, "skills", Skill, lambda _: None)
    assert len(page) == 0


def test_build_aip_page_raises_when_items_key_not_a_list():
    with pytest.raises(ModusError, match="'skills' must be a list"):
        build_aip_page({"skills": {"id": 1}}, "skills", Skill, lambda _: None)
