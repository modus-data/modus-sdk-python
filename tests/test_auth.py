"""Tests for API key resolution and auth header generation."""

import pytest
from modus._auth import auth_headers, resolve_api_key
from modus._exceptions import AuthenticationError


def test_resolve_from_argument():
    assert resolve_api_key("modus_abc123") == "modus_abc123"


def test_resolve_from_env(monkeypatch):
    monkeypatch.setenv("MODUS_API_KEY", "modus_fromenv")
    assert resolve_api_key(None) == "modus_fromenv"


def test_argument_takes_precedence_over_env(monkeypatch):
    monkeypatch.setenv("MODUS_API_KEY", "modus_fromenv")
    assert resolve_api_key("modus_fromarg") == "modus_fromarg"


def test_missing_key_raises(monkeypatch):
    monkeypatch.delenv("MODUS_API_KEY", raising=False)
    with pytest.raises(AuthenticationError, match="No API key provided"):
        resolve_api_key(None)


def test_wrong_prefix_raises():
    bad_key = "sk-openai-wrong"
    with pytest.raises(AuthenticationError, match="Invalid API key format") as exc:
        resolve_api_key(bad_key)
    assert bad_key not in str(exc.value)


def test_wrong_prefix_includes_hint():
    bad_key = "bad_key_format"
    with pytest.raises(AuthenticationError, match="modus_") as exc:
        resolve_api_key(bad_key)
    assert bad_key not in str(exc.value)


def test_auth_headers_format():
    headers = auth_headers("modus_mykey")
    assert headers == {"Authorization": "Bearer modus_mykey"}
