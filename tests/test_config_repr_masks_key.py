from modus._config import ModusConfig


def test_repr_masks_api_key():
    cfg = ModusConfig(api_key="modus_supersecrettoken123")
    r = repr(cfg)
    assert "supersecrettoken123" not in r
    assert "modus_" in r  # prefix still visible
    assert "***" in r


def test_repr_shows_base_url():
    cfg = ModusConfig(api_key="modus_test", base_url="http://localhost:3080")
    assert "localhost:3080" in repr(cfg)
