"""Fixtures for contract tests (OpenAPI + respx clients)."""
from __future__ import annotations

import json
from pathlib import Path

import pytest
from modus import Modus
from modus.management import ModusManagement

from .list_operations import OPENAPI_RELATIVE

# tests/contract/ is one level deeper than tests/test_openapi_drift.py (parents[5]).
_OPENAPI_PATH = Path(__file__).parents[6] / OPENAPI_RELATIVE

pytestmark = pytest.mark.skipif(
    not _OPENAPI_PATH.exists(),
    reason="openapi/v1.json not found — contract tests only run inside the monorepo",
)

TEST_BASE_URL = "https://api.modus.com"
TEST_API_KEY = "modus_test_key_abc123"
TEST_MGMT_API_KEY = "modus_test_mgmt_key_abc123"


@pytest.fixture(scope="module")
def openapi() -> dict:
    return json.loads(_OPENAPI_PATH.read_text())


@pytest.fixture
def contract_client() -> Modus:
    return Modus(api_key=TEST_API_KEY, base_url=TEST_BASE_URL)


@pytest.fixture
def contract_management_client() -> ModusManagement:
    return ModusManagement(api_key=TEST_MGMT_API_KEY, base_url=TEST_BASE_URL)
