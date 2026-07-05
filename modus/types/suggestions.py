"""Types for suggested-question APIs."""
from __future__ import annotations

from modus._generated.models import (
    SuggestionEventSource,
    SuggestionEventType,
    SuggestionQuestionDto,
)

SuggestionQuestion = SuggestionQuestionDto

__all__ = [
    "SuggestionEventSource",
    "SuggestionEventType",
    "SuggestionQuestion",
]
