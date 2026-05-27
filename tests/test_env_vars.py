"""Tests for MODUS_TIMEOUT and MODUS_MAX_RETRIES environment variables."""

import pytest
from modus import Modus, AsyncModus


def test_modus_timeout_env_var(monkeypatch):
    """Test that MODUS_TIMEOUT env var sets the timeout."""
    monkeypatch.setenv("MODUS_TIMEOUT", "120")
    monkeypatch.setenv("MODUS_API_KEY", "modus_testkey")
    client = Modus()
    assert client._config.timeout == 120.0


def test_modus_max_retries_env_var(monkeypatch):
    """Test that MODUS_MAX_RETRIES env var sets max_retries."""
    monkeypatch.setenv("MODUS_MAX_RETRIES", "5")
    monkeypatch.setenv("MODUS_API_KEY", "modus_testkey")
    client = Modus()
    assert client._config.max_retries == 5


def test_explicit_args_override_env_vars(monkeypatch):
    """Test that explicit arguments take precedence over env vars."""
    monkeypatch.setenv("MODUS_TIMEOUT", "99")
    monkeypatch.setenv("MODUS_MAX_RETRIES", "9")
    monkeypatch.setenv("MODUS_API_KEY", "modus_testkey")
    client = Modus(timeout=30, max_retries=1)
    assert client._config.timeout == 30
    assert client._config.max_retries == 1


def test_async_modus_timeout_env_var(monkeypatch):
    """Test that MODUS_TIMEOUT env var sets the timeout on AsyncModus."""
    monkeypatch.setenv("MODUS_TIMEOUT", "150")
    monkeypatch.setenv("MODUS_API_KEY", "modus_testkey")
    client = AsyncModus()
    assert client._config.timeout == 150.0


def test_async_modus_max_retries_env_var(monkeypatch):
    """Test that MODUS_MAX_RETRIES env var sets max_retries on AsyncModus."""
    monkeypatch.setenv("MODUS_MAX_RETRIES", "7")
    monkeypatch.setenv("MODUS_API_KEY", "modus_testkey")
    client = AsyncModus()
    assert client._config.max_retries == 7


def test_invalid_timeout_falls_back_to_default(monkeypatch):
    """Test that invalid MODUS_TIMEOUT falls back to default."""
    monkeypatch.setenv("MODUS_TIMEOUT", "not_a_number")
    monkeypatch.setenv("MODUS_API_KEY", "modus_testkey")
    client = Modus()
    # Should fall back to default timeout (httpx.Timeout object)
    assert client._config.timeout is not None


def test_invalid_max_retries_falls_back_to_default(monkeypatch):
    """Test that invalid MODUS_MAX_RETRIES falls back to default."""
    monkeypatch.setenv("MODUS_MAX_RETRIES", "not_an_int")
    monkeypatch.setenv("MODUS_API_KEY", "modus_testkey")
    client = Modus()
    assert client._config.max_retries == 2  # DEFAULT_MAX_RETRIES


def test_no_env_vars_uses_defaults(monkeypatch):
    """Test that missing env vars uses defaults."""
    monkeypatch.delenv("MODUS_TIMEOUT", raising=False)
    monkeypatch.delenv("MODUS_MAX_RETRIES", raising=False)
    monkeypatch.setenv("MODUS_API_KEY", "modus_testkey")
    client = Modus()
    assert client._config.max_retries == 2  # DEFAULT_MAX_RETRIES
    assert client._config.timeout is not None  # httpx.Timeout object
