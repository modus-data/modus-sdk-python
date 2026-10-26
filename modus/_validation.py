"""Tiny client-side validators shared across resources.

These exist so we fail fast on obvious bad inputs (empty IDs, negative limits)
before making a network call. They raise ``modus.ValidationError`` (a ``ModusError``
and a ``ValueError``): caller-visible bugs, not server-side conditions.
"""
from __future__ import annotations

from typing import Optional, Union

from ._exceptions import ValidationError

# API max page size for context list and values surfaces.
DEFAULT_MAX_PAGE_SIZE = 200


def validate_page_size(page_size: int, *, max_page_size: Optional[int] = None) -> None:
    """Reject page_size values that the backend would reject anyway, locally."""
    if not isinstance(page_size, int) or isinstance(page_size, bool) or page_size < 1:
        raise ValidationError(f"page_size must be a positive int, got {page_size!r}")
    if max_page_size is not None and page_size > max_page_size:
        raise ValidationError(
            f"page_size must be <= {max_page_size}, got {page_size!r}"
        )


def validate_id(resource_id: Union[int, str], *, name: str = "id") -> None:
    """Reject ids that would not address one resource.

    Blank ids hit the list route, and ``.`` / ``..`` are dot segments the URL
    collapses onto the parent (``memories(7).delete('..')`` deleted scope 7).
    """
    if not isinstance(resource_id, str):
        return
    if not resource_id.strip():
        raise ValidationError(f"{name} must be a non-empty string or int")
    if resource_id in (".", ".."):
        raise ValidationError(f"{name} must not be {resource_id!r}")


# Canonical chat model ids from SkillChatRequestDto (keep in sync with the API spec).
ALLOWED_CHAT_MODELS = frozenset({
    "claude-sonnet-5",
    "claude-sonnet-5.5",
    "claude-sonnet-4.6",
    "claude-opus-4.8",
    "claude-opus-5.5",
    "gpt-5.2",
    "gpt-5.5",
    "gpt-5-mini",
    "gpt-5.6-luna",
    "gpt-6-luna",
    "gpt-oss-120b",
    "gpt-oss-20b",
    "qwen3-235b-a22b-2507",
    "qwen3-coder",
    "qwen3-32b",
    "deepseek-chat-v3.1",
    "deepseek-v4-pro",
    "deepseek-v4-flash-latest",
    "deepseek-v4.1-flash-1017",
    "minimax-m2.7",
    "llama-4-maverick",
    "llama-4-scout",
    "llama-3.3-70b-instruct",
    "gemini-3.1-pro-preview",
    "gemini-3-flash-preview",
    "grok-4.3-fast",
    "grok-4.3",
    "grok-4.7",
    "kimi-k3",
})


def validate_chat_model(model: str) -> None:
    if model not in ALLOWED_CHAT_MODELS:
        supported = ", ".join(sorted(ALLOWED_CHAT_MODELS))
        raise ValidationError(
            f"Unsupported model {model!r}. Choose one of: {supported}."
        )
