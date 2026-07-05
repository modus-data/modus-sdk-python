import httpx
import pytest
from modus._http import _raise_for_status


def resp(status, body=None, headers=None):
    import json
    content = json.dumps(body or {}).encode()
    return httpx.Response(status, content=content, headers=headers or {})


def test_request_id_attached_to_error():
    with pytest.raises(Exception) as exc_info:
        _raise_for_status(resp(404, {"message": "not found"}, {"x-request-id": "req_abc123"}))
    err = exc_info.value
    assert hasattr(err, "request_id")
    assert err.request_id == "req_abc123"


def test_request_id_none_when_header_absent():
    with pytest.raises(Exception) as exc_info:
        _raise_for_status(resp(404, {"message": "not found"}))
    assert exc_info.value.request_id is None


def test_request_id_case_insensitive():
    with pytest.raises(Exception) as exc_info:
        _raise_for_status(resp(500, {"message": "oops"}, {"X-Request-ID": "req_xyz"}))
    assert exc_info.value.request_id == "req_xyz"
