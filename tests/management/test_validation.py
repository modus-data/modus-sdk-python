"""Tests for client-side input validation in the management SDK.

These verify that obvious bad inputs fail fast with a ValueError, before any
network call is made. CodeRabbit findings #1, #2, #3, #4, #A propagated for
parity with the consumption SDK.
"""
from __future__ import annotations

import pytest
import respx
from modus.management import ModusManagement
from modus._config import ModusConfig


def _client() -> ModusManagement:
    return ModusManagement(api_key="modus_test_key", base_url="https://api.modus.com")


# ---- max_retries validated at config construction (#A) -----------------------

def test_config_rejects_negative_max_retries():
    with pytest.raises(ValueError, match="max_retries must be a non-negative int"):
        ModusConfig(api_key="modus_test_key", max_retries=-1)


def test_config_rejects_bool_max_retries():
    with pytest.raises(ValueError, match="max_retries must be a non-negative int"):
        ModusConfig(api_key="modus_test_key", max_retries=True)  # type: ignore[arg-type]


def test_config_accepts_zero_max_retries():
    cfg = ModusConfig(api_key="modus_test_key", max_retries=0)
    assert cfg.max_retries == 0


# ---- limit validation on list endpoints --------------------------------------

@respx.mock
def test_skills_list_rejects_zero_limit():
    with pytest.raises(ValueError, match="limit must be a positive int"):
        _client().skills.list(limit=0)
    assert not respx.calls


@respx.mock
def test_agents_list_rejects_negative_limit():
    with pytest.raises(ValueError, match="limit must be a positive int"):
        _client().agents.list(limit=-3)
    assert not respx.calls


# ---- empty-id validation on id-taking endpoints ------------------------------

@respx.mock
def test_skills_get_rejects_empty_string():
    with pytest.raises(ValueError, match="skill_id must be a non-empty"):
        _client().skills.get("")
    assert not respx.calls


@respx.mock
def test_skills_update_rejects_empty_string():
    with pytest.raises(ValueError, match="skill_id must be a non-empty"):
        _client().skills.update("", name="x")
    assert not respx.calls


@respx.mock
def test_skills_deploy_rejects_empty_string():
    with pytest.raises(ValueError, match="skill_id must be a non-empty"):
        _client().skills.deploy("")
    assert not respx.calls


@respx.mock
def test_skills_delete_rejects_empty_string():
    with pytest.raises(ValueError, match="skill_id must be a non-empty"):
        _client().skills.delete("")
    assert not respx.calls


@respx.mock
def test_agents_get_rejects_whitespace():
    with pytest.raises(ValueError, match="agent_id must be a non-empty"):
        _client().agents.get("   ")
    assert not respx.calls
