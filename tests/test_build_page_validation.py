import pytest
from modus._exceptions import ModusError
from modus._pagination import build_aip_page, resolve_list_items_key
from modus.types.scopes import Scope


def test_build_aip_page_raises_on_missing_items_key():
    with pytest.raises(ModusError, match="missing 'scopes'"):
        build_aip_page({"error": "unexpected"}, "scopes", Scope, lambda _: None)


def test_build_aip_page_raises_on_non_dict():
    with pytest.raises(ModusError, match="missing 'scopes'"):
        build_aip_page([], "scopes", Scope, lambda _: None)


def test_build_aip_page_ok_with_empty_items():
    page = build_aip_page({"scopes": [], "nextPageToken": None}, "scopes", Scope, lambda _: None)
    assert len(page) == 0


def test_build_aip_page_raises_when_items_key_not_a_list():
    with pytest.raises(ModusError, match="'scopes' must be a list"):
        build_aip_page({"scopes": {"id": 1}}, "scopes", Scope, lambda _: None)


def test_resolve_list_items_key_prefers_canonical():
    data = {"scopes": [], "workflows": [{"id": 1}]}
    assert resolve_list_items_key(data, "scopes", "workflows") == "scopes"


def test_resolve_list_items_key_uses_fallback_when_preferred_missing():
    data = {"workflows": [{"id": 1}]}
    assert resolve_list_items_key(data, "scopes", "workflows") == "workflows"


def test_resolve_list_items_key_defaults_to_preferred_when_missing():
    data: dict = {}
    assert resolve_list_items_key(data, "scopes", "workflows") == "scopes"
