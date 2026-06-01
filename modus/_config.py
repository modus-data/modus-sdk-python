"""
SDK configuration.

ModusConfig holds all settings for a client instance. It is created once
during Modus.__init__ and passed down to the HTTP client and all resources.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Union

import httpx

# Defaults — override via Modus(base_url=..., timeout=..., max_retries=...)
DEFAULT_BASE_URL = "https://api.modus.com"


def _default_timeout() -> httpx.Timeout:
    """Factory function to create the default timeout object."""
    return httpx.Timeout(
        connect=5.0,
        read=300.0,
        write=10.0,
        pool=5.0,
    )


DEFAULT_TIMEOUT: Union[float, httpx.Timeout] = _default_timeout()
DEFAULT_MAX_RETRIES = 2  # retried on 429 + 5xx only


@dataclass(frozen=True)
class ModusConfig:
    api_key: str
    base_url: str = DEFAULT_BASE_URL
    timeout: Union[float, httpx.Timeout] = field(default_factory=_default_timeout)
    max_retries: int = DEFAULT_MAX_RETRIES

    def __post_init__(self) -> None:
        # Reject obviously-bad max_retries early — negative/non-int would later
        # bottom out in `range(max_retries + 1)` yielding zero attempts and a
        # confusing "unreachable" RuntimeError from the retry loop.
        if not isinstance(self.max_retries, int) or isinstance(self.max_retries, bool) or self.max_retries < 0:
            raise ValueError(
                f"max_retries must be a non-negative int, got {self.max_retries!r}"
            )
        # frozen=True prevents self.base_url = ... — use object.__setattr__
        object.__setattr__(self, "base_url", self.base_url.rstrip("/"))

    def __repr__(self) -> str:
        masked = f"{self.api_key[:10]}***" if len(self.api_key) > 10 else "***"
        return (
            f"ModusConfig(api_key={masked!r}, base_url={self.base_url!r}, "
            f"timeout={self.timeout!r}, max_retries={self.max_retries!r})"
        )
