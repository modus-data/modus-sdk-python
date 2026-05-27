"""Tests for HTTP status code → exception mapping and exception instantiation."""

from __future__ import annotations

import json
import pytest
import httpx
from modus._http import _raise_for_status, _wrap_connect_error
from modus._exceptions import (
    AuthenticationError,
    ConflictError,
    InternalServerError,
    ModusError,
    NotFoundError,
    PermissionDeniedError,
    RateLimitError,
    UnprocessableError,
)


def resp(
    status: int,
    body: dict | None = None,
    headers: dict | None = None,
) -> httpx.Response:
    content = json.dumps(body or {}).encode()
    return httpx.Response(status, content=content, headers=headers or {})


def test_2xx_does_not_raise():
    _raise_for_status(resp(200))
    _raise_for_status(resp(201))
    _raise_for_status(resp(204, {}))


def test_401_authentication_error():
    with pytest.raises(AuthenticationError) as exc:
        _raise_for_status(resp(401, {"message": "Invalid token"}))
    assert exc.value.status_code == 401
    assert "Invalid token" in exc.value.message


def test_403_permission_error():
    with pytest.raises(PermissionDeniedError) as exc:
        _raise_for_status(resp(403, {"message": "Forbidden"}))
    assert exc.value.status_code == 403


def test_404_not_found():
    with pytest.raises(NotFoundError) as exc:
        _raise_for_status(resp(404, {"message": "Skill not found"}))
    assert exc.value.status_code == 404
    assert "Skill not found" in exc.value.message


def test_409_conflict():
    with pytest.raises(ConflictError) as exc:
        _raise_for_status(resp(409, {"message": "Run already exists"}))
    assert exc.value.status_code == 409


def test_422_unprocessable():
    with pytest.raises(UnprocessableError):
        _raise_for_status(resp(422, {"message": "Validation failed"}))


def test_429_rate_limit_no_header():
    with pytest.raises(RateLimitError) as exc:
        _raise_for_status(resp(429, {"message": "Too many requests"}))
    assert exc.value.retry_after is None


def test_429_rate_limit_with_retry_after():
    with pytest.raises(RateLimitError) as exc:
        _raise_for_status(resp(429, {"message": "Slow down"}, {"retry-after": "30"}))
    assert exc.value.retry_after == 30


def test_500_internal_server_error():
    with pytest.raises(InternalServerError) as exc:
        _raise_for_status(resp(500, {"message": "Something broke"}))
    assert exc.value.status_code == 500


def test_503_also_internal_server_error():
    with pytest.raises(InternalServerError):
        _raise_for_status(resp(503))


def test_unknown_4xx_is_modus_error():
    with pytest.raises(ModusError) as exc:
        _raise_for_status(resp(418, {"message": "I'm a teapot"}))
    assert exc.value.status_code == 418


def test_nestjs_list_message_joined():
    # NestJS 422 returns message as list
    with pytest.raises(UnprocessableError) as exc:
        _raise_for_status(resp(422, {"message": ["field is required", "must be string"]}))
    assert "field is required" in exc.value.message


# ---------------------------------------------------------------------------
# Direct exception instantiation — status codes are baked in per subclass
# ---------------------------------------------------------------------------


def test_authentication_error_status_code():
    assert AuthenticationError("bad token").status_code == 401


def test_permission_denied_error_status_code():
    assert PermissionDeniedError("forbidden").status_code == 403


def test_not_found_error_status_code():
    assert NotFoundError("missing").status_code == 404


def test_conflict_error_status_code():
    assert ConflictError("duplicate").status_code == 409


def test_unprocessable_error_status_code():
    assert UnprocessableError("invalid").status_code == 422


def test_rate_limit_error_status_code():
    assert RateLimitError("slow down").status_code == 429


def test_internal_server_error_requires_status_code():
    """InternalServerError must receive an explicit status_code (covers 5xx range)."""
    err = InternalServerError("broke", status_code=503)
    assert err.status_code == 503
    assert err.message == "broke"


def test_internal_server_error_missing_status_code_raises():
    with pytest.raises(TypeError):
        InternalServerError("broke")  # status_code is required keyword arg


def test_modus_error_base_message_and_status():
    err = ModusError("something went wrong", status_code=418)
    assert err.message == "something went wrong"
    assert err.status_code == 418
    assert "418" in repr(err)


# ---------------------------------------------------------------------------
# _wrap_connect_error — connection failure carries the target URL
# ---------------------------------------------------------------------------


def test_wrap_connect_error_includes_base_url():
    raw = httpx.ConnectError("Connection refused")
    wrapped = _wrap_connect_error(raw, "https://api.modus.com")
    assert isinstance(wrapped, ModusError)
    assert "https://api.modus.com" in wrapped.message


def test_wrap_connect_error_mentions_env_var():
    raw = httpx.ConnectError("getaddrinfo failed")
    wrapped = _wrap_connect_error(raw, "http://localhost:3000")
    assert "MODUS_BASE_URL" in wrapped.message
