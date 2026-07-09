"""Evaluation configuration and run types."""

from __future__ import annotations

from modus._generated.models import (
    EvaluationConfigDto,
    EvaluationRunDto,
    EvaluationRunWithResultsDto,
    TriggerEvaluationRunResponseDto,
    UpdateEvaluationConfigDto,
)

EvaluationConfig = EvaluationConfigDto
UpdateEvaluationConfig = UpdateEvaluationConfigDto
EvaluationRun = EvaluationRunDto
EvaluationRunWithResults = EvaluationRunWithResultsDto
TriggerEvaluationRunResponse = TriggerEvaluationRunResponseDto

__all__ = [
    "EvaluationConfig",
    "UpdateEvaluationConfig",
    "EvaluationRun",
    "EvaluationRunWithResults",
    "TriggerEvaluationRunResponse",
]
