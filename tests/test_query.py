"""Tests for the updateMask URL helper."""
import pytest
from modus._query import with_update_mask


def test_none_returns_path_unchanged():
    assert with_update_mask("/api/v1/skills/1", None) == "/api/v1/skills/1"


@pytest.mark.parametrize("bad", ["", "   ", "\t"])
def test_empty_or_whitespace_mask_raises(bad):
    with pytest.raises(ValueError, match="non-empty"):
        with_update_mask("/api/v1/skills/1", bad)


def test_appends_query_when_no_existing_query():
    assert with_update_mask("/api/v1/skills/1", "name,model") == "/api/v1/skills/1?updateMask=name%2Cmodel"


def test_uses_ampersand_when_query_present():
    out = with_update_mask("/api/v1/skills/1?foo=bar", "name")
    assert out == "/api/v1/skills/1?foo=bar&updateMask=name"
