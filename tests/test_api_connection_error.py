import pytest
from unittest.mock import MagicMock
from modus._exceptions import APIConnectionError, ModusError
from modus._retry import with_retry


def test_api_connection_error_is_modus_error():
    err = APIConnectionError("network failed")
    assert isinstance(err, ModusError)
    assert "network failed" in str(err)


def test_api_connection_error_is_retried(monkeypatch):
    monkeypatch.setattr("time.sleep", lambda _: None)
    fn = MagicMock(side_effect=[APIConnectionError("fail"), "ok"])
    result = with_retry(fn, max_retries=2)
    assert result == "ok"
    assert fn.call_count == 2


def test_api_connection_error_exhausted_raises(monkeypatch):
    monkeypatch.setattr("time.sleep", lambda _: None)
    fn = MagicMock(side_effect=APIConnectionError("always fails"))
    with pytest.raises(APIConnectionError):
        with_retry(fn, max_retries=2)
    assert fn.call_count == 3
