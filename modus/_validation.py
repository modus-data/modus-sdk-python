"""Tiny client-side validators shared across resources.

These exist so we fail fast on obvious bad inputs (empty IDs, negative limits)
before making a network call. They raise ``ValueError`` — caller-visible bugs,
not server-side conditions.
"""
from __future__ import annotations
from typing import Union


def validate_limit(limit: int) -> None:
    """Reject limit values that the backend would reject anyway, locally."""
    if not isinstance(limit, int) or isinstance(limit, bool) or limit < 1:
        raise ValueError(f"limit must be a positive int, got {limit!r}")


def validate_id(resource_id: Union[int, str], *, name: str = "id") -> None:
    """Reject empty/whitespace-only string IDs that would produce ambiguous URLs."""
    if isinstance(resource_id, str) and not resource_id.strip():
        raise ValueError(f"{name} must be a non-empty string or int")


# Canonical model ids from OpenAPI SkillChatRequestDto (keep in sync with modus-api).
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
    "grok-4",
    "grok-4.1-fast",
})


def validate_chat_model(model: str) -> None:
    if model not in ALLOWED_CHAT_MODELS:
        raise ValueError(
            f"model must be one of the canonical ids allowed by the API "
            f"(e.g. claude-sonnet-4.6), got {model!r}"
        )
