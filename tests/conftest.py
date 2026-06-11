"""Shared fixtures for all tests."""

import pytest
from modus import AsyncModus, Modus
from tests.fixtures.api_shapes import SAMPLE_AGENT, SAMPLE_CONTEXT_ITEM, SAMPLE_SKILL

TEST_API_KEY = "modus_test_key_abc123"
TEST_BASE_URL = "https://api.modus.com"


@pytest.fixture
def client() -> Modus:
    return Modus(api_key=TEST_API_KEY, base_url=TEST_BASE_URL)


@pytest.fixture
def async_client() -> AsyncModus:
    return AsyncModus(api_key=TEST_API_KEY, base_url=TEST_BASE_URL)


@pytest.fixture
def sample_skill() -> dict:
    return dict(SAMPLE_SKILL)


@pytest.fixture
def sample_agent() -> dict:
    return dict(SAMPLE_AGENT)


@pytest.fixture
def sample_context_item() -> dict:
    return dict(SAMPLE_CONTEXT_ITEM)
