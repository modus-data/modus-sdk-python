import pytest
from dataclasses import FrozenInstanceError
from modus._config import ModusConfig


def test_config_is_frozen():
    cfg = ModusConfig(api_key="modus_test")
    with pytest.raises(FrozenInstanceError):
        cfg.api_key = "modus_other"


def test_config_base_url_normalized():
    cfg = ModusConfig(api_key="modus_test", base_url="https://api.modus.com/")
    assert not cfg.base_url.endswith("/")
