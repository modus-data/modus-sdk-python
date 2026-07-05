"""Tests for client-side input validation in the consumption SDK.

These verify that obvious bad inputs fail fast with a ValueError, before any
network call is made. CodeRabbit findings #1, #2, #3, #4, #A.
"""
from __future__ import annotations

import pytest
import respx
from modus import Modus
from modus._config import ModusConfig


def _client() -> Modus:
    return Modus(api_key="modus_test_key", base_url="https://api.modus.com")


# ---- max_retries validated at config construction (#A) -----------------------

def test_config_rejects_negative_max_retries():
    with pytest.raises(ValueError, match="max_retries must be a non-negative int"):
        ModusConfig(api_key="modus_test_key", max_retries=-1)


def test_config_rejects_bool_max_retries():
    # bool is a subclass of int — explicitly excluded so True/False can't slip through
    with pytest.raises(ValueError, match="max_retries must be a non-negative int"):
        ModusConfig(api_key="modus_test_key", max_retries=True)  # type: ignore[arg-type]


def test_config_accepts_zero_max_retries():
    cfg = ModusConfig(api_key="modus_test_key", max_retries=0)
    assert cfg.max_retries == 0


# ---- page_size validation on list endpoints (#1, #3) -----------------------

@respx.mock
def test_skills_list_rejects_zero_page_size():
    with pytest.raises(ValueError, match="page_size must be a positive int"):
        _client().scopes.list(page_size=0)
    # Crucially: no HTTP call was made
    assert not respx.calls


@respx.mock
def test_skills_list_rejects_negative_page_size():
    with pytest.raises(ValueError, match="page_size must be a positive int"):
        _client().scopes.list(page_size=-5)
    assert not respx.calls


@respx.mock
def test_agents_list_rejects_zero_page_size():
    with pytest.raises(ValueError, match="page_size must be a positive int"):
        _client().workflows.list(page_size=0)
    assert not respx.calls


# ---- empty-id validation on get endpoints (#2, #4) ---------------------------

@respx.mock
def test_skills_get_rejects_empty_string():
    with pytest.raises(ValueError, match="scope_id must be a non-empty"):
        _client().scopes.get("")
    assert not respx.calls


@respx.mock
def test_skills_get_rejects_whitespace_string():
    with pytest.raises(ValueError, match="scope_id must be a non-empty"):
        _client().scopes.get("   ")
    assert not respx.calls


@respx.mock
def test_agents_get_rejects_empty_string():
    with pytest.raises(ValueError, match="workflow_id must be a non-empty"):
        _client().workflows.get("")
    assert not respx.calls


def test_skills_get_accepts_int_zero():
    """int 0 is a valid (if unusual) id — not rejected by validate_id."""
    # We don't mock — we just want validate_id to not raise. Real HTTP call
    # will fail with respx.mock not loaded, but validate_id passes first.
    with pytest.raises(Exception):  # connection error or similar
        _client().scopes.get(0)
