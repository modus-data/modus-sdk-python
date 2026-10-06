"""
SDK configuration.

ModusConfig holds all settings for a client instance. It is created once
during Modus.__init__ and passed down to the HTTP client and all resources.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Mapping, Optional, Union

import httpx

# Defaults — override via Modus(base_url=..., agent_host=..., timeout=..., max_retries=...)
DEFAULT_BASE_URL = "https://api.getmodus.com"
DEFAULT_AGENT_HOST = "https://agent.getmodus.com"


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


def _normalize_base_url(value: str) -> str:
    return value.rstrip("/")


def _normalize_base_urls(value: Mapping[str, str]) -> Mapping[str, str]:
    return MappingProxyType(
        {service: _normalize_base_url(base_url) for service, base_url in value.items()}
    )


@dataclass(frozen=True)
class ModusConfig:
    api_key: str
    base_url: str = DEFAULT_BASE_URL
    timeout: Union[float, httpx.Timeout] = field(default_factory=_default_timeout)
    max_retries: int = DEFAULT_MAX_RETRIES
    agent_host: Optional[str] = None
    organization_id: Optional[str] = None
    base_urls: Mapping[str, str] = field(default_factory=dict)
    default_headers: Optional[Mapping[str, str]] = None

    def __post_init__(self) -> None:
        # Reject obviously-bad max_retries early — negative/non-int would later
        # bottom out in `range(max_retries + 1)` yielding zero attempts and a
        # confusing "unreachable" RuntimeError from the retry loop.
        if not isinstance(self.max_retries, int) or isinstance(self.max_retries, bool) or self.max_retries < 0:
            raise ValueError(
                f"max_retries must be a non-negative int, got {self.max_retries!r}"
            )
        # frozen=True prevents self.base_url = ... — use object.__setattr__
        object.__setattr__(self, "base_url", _normalize_base_url(self.base_url))
        if self.agent_host is not None:
            object.__setattr__(self, "agent_host", _normalize_base_url(self.agent_host))
        if self.organization_id is not None:
            object.__setattr__(self, "organization_id", self.organization_id.strip() or None)
        object.__setattr__(self, "base_urls", _normalize_base_urls(self.base_urls))
        object.__setattr__(self, "default_headers", MappingProxyType(dict(self.default_headers or {})))

    def __repr__(self) -> str:
        masked = f"{self.api_key[:10]}***" if len(self.api_key) > 10 else "***"
        return (
            f"ModusConfig(api_key={masked!r}, base_url={self.base_url!r}, "
            f"timeout={self.timeout!r}, max_retries={self.max_retries!r})"
        )


def resolve_service_base_url(
    config: ModusConfig,
    service: str,
    server_url: Optional[str],
) -> str:
    """Return the origin for an operation's owning public service."""
    if service == "modus-api":
        return config.base_url
    if service in config.base_urls:
        return config.base_urls[service]
    if service == "agent-service" and config.agent_host:
        return config.agent_host
    if server_url:
        return _normalize_base_url(server_url)
    return config.base_url
