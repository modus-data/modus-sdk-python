import httpx
from modus import Modus
from modus._config import DEFAULT_TIMEOUT


def test_default_timeout_is_httpx_timeout_object():
    assert isinstance(DEFAULT_TIMEOUT, httpx.Timeout)


def test_default_connect_timeout_is_5s():
    assert DEFAULT_TIMEOUT.connect == 5.0


def test_default_read_timeout_is_300s():
    assert DEFAULT_TIMEOUT.read == 300.0


def test_simple_float_timeout_accepted():
    client = Modus(api_key="modus_test", timeout=120)
    assert client._config.timeout == 120


def test_httpx_timeout_object_accepted():
    t = httpx.Timeout(connect=2.0, read=600.0, write=10.0, pool=5.0)
    client = Modus(api_key="modus_test", timeout=t)
    assert client._config.timeout is t
