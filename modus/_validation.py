"""Tiny client-side validators shared across resources.

These exist so we fail fast on obvious bad inputs (empty IDs, negative limits)
before making a network call. They raise ``ValueError`` — caller-visible bugs,
not server-side conditions.
"""
from __future__ import annotations

from typing import Optional, Union

# API max page size for context list and values surfaces.
DEFAULT_MAX_PAGE_SIZE = 200


def validate_page_size(page_size: int, *, max_page_size: Optional[int] = None) -> None:
    """Reject page_size values that the backend would reject anyway, locally."""
    if not isinstance(page_size, int) or isinstance(page_size, bool) or page_size < 1:
        raise ValueError(f"page_size must be a positive int, got {page_size!r}")
    if max_page_size is not None and page_size > max_page_size:
        raise ValueError(
            f"page_size must be <= {max_page_size}, got {page_size!r}"
        )


def validate_id(resource_id: Union[int, str], *, name: str = "id") -> None:
    """Reject empty/whitespace-only string IDs that would produce ambiguous URLs."""
    if isinstance(resource_id, str) and not resource_id.strip():
        raise ValueError(f"{name} must be a non-empty string or int")


# Canonical chat model ids from SkillChatRequestDto (keep in sync with the API spec).
ALLOWED_CHAT_MODELS = frozenset({
    "claude-sonnet-4.6",
    "claude-opus-4.8",
    "gpt-5.2",
    "gpt-5.5",
    "gpt-5-mini",
    "gpt-oss-120b",
    "gpt-oss-20b",
    "qwen3-235b-a22b-2507",
    "qwen3-coder",
    "qwen3-32b",
    "deepseek-chat-v3.1",
    "minimax-m2.7",
    "llama-4-maverick",
    "llama-4-scout",
    "llama-3.3-70b-instruct",
    "gemini-3.1-pro-preview",
    "gemini-3-flash-preview",
    "grok-4.3-fast",
    "grok-4.3",
})


def validate_chat_model(model: str) -> None:
    if model not in ALLOWED_CHAT_MODELS:
        supported = ", ".join(sorted(ALLOWED_CHAT_MODELS))
        raise ValueError(
            f"Unsupported model {model!r}. Choose one of: {supported}."
        )
