from unittest.mock import MagicMock

import pytest
from modus._exceptions import APIConnectionError, ModusError
from modus._retry import with_retry


def test_api_connection_error_is_modus_error():
    err = APIConnectionError("network failed")
    assert isinstance(err, ModusError)
    assert "network failed" in str(err)


def test_api_connection_error_is_retried(monkeypatch):
    monkeypatch.setattr("time.sleep", lambda _: None)
    fn = MagicMock(side_effect=[APIConnectionError("fail", retryable=True), "ok"])
    result = with_retry(fn, max_retries=2)
    assert result == "ok"
    assert fn.call_count == 2


def test_api_connection_error_exhausted_raises(monkeypatch):
    monkeypatch.setattr("time.sleep", lambda _: None)
    fn = MagicMock(side_effect=APIConnectionError("always fails", retryable=True))
    with pytest.raises(APIConnectionError):
        with_retry(fn, max_retries=2)
    assert fn.call_count == 3


def test_api_connection_error_not_retryable_raises_at_once(monkeypatch):
    monkeypatch.setattr("time.sleep", lambda _: None)
    fn = MagicMock(side_effect=APIConnectionError("post may have run"))
    with pytest.raises(APIConnectionError):
        with_retry(fn, max_retries=2)
    assert fn.call_count == 1
