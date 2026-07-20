"""
API key resolution and auth header generation.

The SDK accepts an API key via:
  1. Explicit argument: Modus(api_key="modus_xxx")
  2. Environment variable: MODUS_API_KEY=modus_xxx

The SDK validates the key format at initialization time so users get a
clear error immediately rather than a cryptic 401 on the first request.
"""

from __future__ import annotations

import os
from typing import Optional, Union

import httpx

from ._exceptions import AuthenticationError

_ENV_VAR = "MODUS_API_KEY"
_BASE_URL_ENV_VAR = "MODUS_BASE_URL"
_AGENT_HOST_ENV_VAR = "MODUS_AGENT_HOST"
_ORGANIZATION_ID_ENV_VAR = "MODUS_ORGANIZATION_ID"
_TIMEOUT_ENV_VAR = "MODUS_TIMEOUT"
_MAX_RETRIES_ENV_VAR = "MODUS_MAX_RETRIES"
_KEY_PREFIX = "modus_"


def resolve_api_key(api_key: Optional[str]) -> str:
    """
    Resolve the API key from an explicit argument or the environment.
    Raises AuthenticationError if no key is found or the format is invalid.
    """
    key = api_key or os.environ.get(_ENV_VAR)

    if not key:
        raise AuthenticationError(
            f"No API key provided. "
            f"Pass api_key= or set the {_ENV_VAR} environment variable. "
            f"Create a token at app.getmodus.com → Settings → API Tokens."
        )

    if not key.startswith(_KEY_PREFIX):
        raise AuthenticationError(
            f"Invalid API key format. Modus API keys start with '{_KEY_PREFIX}'. "
            f"Create a token at app.getmodus.com → Settings → API Tokens."
        )

    return key


def resolve_base_url(base_url: Optional[str]) -> Optional[str]:
    """
    Resolve the base URL from an explicit constructor argument, or from the
    ``MODUS_BASE_URL`` environment variable when set. Returns ``None`` if
    neither is set (caller uses the production default).
    """
    return base_url or os.environ.get(_BASE_URL_ENV_VAR) or None


def resolve_agent_host(agent_host: Optional[str]) -> Optional[str]:
    """
    Resolve the agent host from an explicit constructor argument, or from the
    ``MODUS_AGENT_HOST`` environment variable when set. Returns ``None`` if
    neither is set (caller uses the production default).
    """
    return agent_host or os.environ.get(_AGENT_HOST_ENV_VAR) or None


def resolve_organization_id(organization_id: Optional[str]) -> Optional[str]:
    """
    Resolve an optional Clerk organization id for agent-host run bodies.
    From ``organization_id=`` or ``MODUS_ORGANIZATION_ID``. Usually omitted —
    agent-service falls back to the PAT principal's org.
    """
    raw = organization_id if organization_id is not None else os.environ.get(_ORGANIZATION_ID_ENV_VAR)
    if raw is None:
        return None
    stripped = raw.strip()
    return stripped or None


def resolve_timeout(explicit: Union[float, httpx.Timeout, None]) -> Union[float, httpx.Timeout, None]:
    """
    Resolve timeout from an explicit argument or the MODUS_TIMEOUT env var.
    Returns None if neither is set (caller will use the default).

    If MODUS_TIMEOUT is set but invalid, returns None (falls back to default).
    """
    if explicit is not None:
        return explicit
    raw = os.environ.get(_TIMEOUT_ENV_VAR)
    if raw is not None:
        try:
            return float(raw)
        except ValueError:
            return None
    return None


def resolve_max_retries(explicit: Optional[int]) -> Optional[int]:
    """
    Resolve max_retries from an explicit argument or the MODUS_MAX_RETRIES env var.
    Returns None if neither is set (caller will use the default).

    If MODUS_MAX_RETRIES is set but invalid, returns None (falls back to default).
    """
    if explicit is not None:
        if explicit < 0:
            raise ValueError(f"max_retries must be >= 0, got {explicit}")
        return explicit
    raw = os.environ.get(_MAX_RETRIES_ENV_VAR)
    if raw is not None:
        try:
            value = int(raw)
            return value if value >= 0 else None
        except ValueError:
            return None
    return None


def auth_headers(api_key: str) -> dict[str, str]:
    """Return the Authorization header dict for a given API key."""
    return {"Authorization": f"Bearer {api_key}"}
