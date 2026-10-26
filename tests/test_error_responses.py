"""Replay the shared error fixtures through the transport.

``distribution/clients/error-responses.json`` is also replayed by the TypeScript suite
(tests/error-responses.test.ts), so both SDKs map every real error the same way.
"""

from __future__ import annotations

import json
from pathlib import Path

import httpx
import pytest
import respx
from modus import ModusError
from modus._config import ModusConfig
from modus._http import HttpClient

_CASES = json.loads(
    (Path(__file__).resolve().parents[3] / "error-responses.json").read_text()
)["cases"]
BASE = "https://api.modus.com"


def _raised(case: dict, method: str) -> ModusError:
    http = HttpClient(ModusConfig(api_key="modus_test_key", base_url=BASE, max_retries=0))
    with respx.mock:
        respx.request(method, f"{BASE}/api/v1/scopes").mock(
            return_value=httpx.Response(
                case["status"], content=case["body"].encode(), headers=case["headers"]
            )
        )
        with pytest.raises(ModusError) as exc:
            if method == "GET":
                http.get("/api/v1/scopes")
            else:
                http.post("/api/v1/scopes", json={})
    return exc.value


@pytest.mark.parametrize("method", ["GET", "POST"])
@pytest.mark.parametrize("case", _CASES, ids=[c["name"] for c in _CASES])
def test_error_response(case: dict, method: str) -> None:
    error = _raised(case, method)
    want = case["expect"]
    assert type(error).__name__ == want["class"]
    assert error.status_code == want["statusCode"]
    assert error.code == want["code"]
    assert error.message == want["message"]
    assert error.request_id == want["requestId"]
    assert error.info == want["info"]
    assert error.body == case["body"]
    if "retryAfter" in want:
        assert error.retry_after == want["retryAfter"]  # type: ignore[attr-defined]
    assert error.retryable is want["retry"][method]
