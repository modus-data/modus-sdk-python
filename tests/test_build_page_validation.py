import pytest
from modus._exceptions import ModusError
from modus._pagination import build_aip_page, resolve_list_items_key
from modus.types.scopes import Scope


def test_build_aip_page_raises_on_missing_items_key():
    with pytest.raises(ModusError, match="missing 'skills'"):
        build_aip_page({"error": "unexpected"}, "skills", Scope, lambda _: None)


def test_build_aip_page_raises_on_non_dict():
    with pytest.raises(ModusError, match="missing 'skills'"):
        build_aip_page([], "skills", Scope, lambda _: None)


def test_build_aip_page_ok_with_empty_items():
    page = build_aip_page({"skills": [], "nextPageToken": None}, "skills", Scope, lambda _: None)
    assert len(page) == 0


def test_build_aip_page_raises_when_items_key_not_a_list():
    with pytest.raises(ModusError, match="'skills' must be a list"):
        build_aip_page({"skills": {"id": 1}}, "skills", Scope, lambda _: None)


def test_resolve_list_items_key_prefers_canonical():
    data = {"scopes": [], "skills": [{"id": 1}]}
    assert resolve_list_items_key(data, "scopes", "skills") == "scopes"


def test_resolve_list_items_key_falls_back_to_deprecated():
    data = {"skills": [{"id": 1}]}
    assert resolve_list_items_key(data, "scopes", "skills") == "skills"


def test_resolve_list_items_key_defaults_to_preferred_when_missing():
    data: dict = {}
    assert resolve_list_items_key(data, "scopes", "skills") == "scopes"
