"""Scheduled and manual skill evaluations for a scope."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Union

from modus._config import ModusConfig
from modus._generated.resources.management.scopes.evaluations import (
    _ScopesEvaluationsResourceBase,
)
from modus._http import HttpClient


@dataclass(frozen=True)
class ScopeEvaluationsOperations:
    get_config: str
    update_config: str
    trigger_run: str
    list_runs: str
    get_run: str


SCOPE_EVALUATION_OPERATIONS = ScopeEvaluationsOperations(
    get_config="EvaluationsController_getConfig",
    update_config="EvaluationsController_updateConfig",
    trigger_run="EvaluationsController_triggerRun",
    list_runs="EvaluationsController_listRuns",
    get_run="EvaluationsController_getRun",
)


class ScopeEvaluationsResource(_ScopesEvaluationsResourceBase):
    def __init__(
        self,
        http: HttpClient,
        config: ModusConfig,
        scope_id: Union[int, str],
        ops: ScopeEvaluationsOperations = SCOPE_EVALUATION_OPERATIONS,
    ) -> None:
        super().__init__(http, config, scope_id, ops)
