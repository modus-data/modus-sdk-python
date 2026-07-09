"""Scheduled and manual skill evaluations for a scope."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Union

from modus._config import ModusConfig
from modus._http import HttpClient
from modus._openapi_invoke import invoke_operation
from modus._pagination import aip_list_params, build_aip_page_mapped
from modus._retry import with_retry
from modus._validation import validate_id, validate_page_size
from modus.management.types.evaluations import (
    EvaluationConfig,
    EvaluationRun,
    EvaluationRunWithResults,
    TriggerEvaluationRunResponse,
    UpdateEvaluationConfig,
)
from modus.types.pagination import Page


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


def _map_config(raw: dict) -> EvaluationConfig:
    return EvaluationConfig.model_validate(raw)


def _map_run(raw: dict) -> EvaluationRun:
    return EvaluationRun.model_validate(raw)


class ScopeEvaluationsResource:
    def __init__(
        self,
        http: HttpClient,
        config: ModusConfig,
        scope_id: Union[int, str],
        ops: ScopeEvaluationsOperations = SCOPE_EVALUATION_OPERATIONS,
    ) -> None:
        self._http = http
        self._config = config
        self._scope_id = scope_id
        self._ops = ops

    def get_config(self) -> EvaluationConfig:
        validate_id(self._scope_id, name="scope_id")
        data = with_retry(
            lambda: invoke_operation(
                self._http,
                self._ops.get_config,
                path_params={"id": self._scope_id},
            ),
            self._config.max_retries,
        )
        return _map_config(data)

    def update_config(self, update: UpdateEvaluationConfig) -> EvaluationConfig:
        validate_id(self._scope_id, name="scope_id")
        data = with_retry(
            lambda: invoke_operation(
                self._http,
                self._ops.update_config,
                path_params={"id": self._scope_id},
                json_body=update.model_dump(exclude_none=True),
            ),
            self._config.max_retries,
        )
        return _map_config(data)

    def trigger_run(self) -> TriggerEvaluationRunResponse:
        validate_id(self._scope_id, name="scope_id")
        data = with_retry(
            lambda: invoke_operation(
                self._http,
                self._ops.trigger_run,
                path_params={"id": self._scope_id},
            ),
            self._config.max_retries,
        )
        return TriggerEvaluationRunResponse.model_validate(data)

    def list_runs(
        self,
        *,
        page_size: int = 25,
        page_token: Optional[str] = None,
    ) -> Page[EvaluationRun]:
        validate_page_size(page_size)
        return self._list_runs_page(page_size, page_token)

    def _list_runs_page(
        self,
        page_size: int,
        page_token: Optional[str],
    ) -> Page[EvaluationRun]:
        validate_id(self._scope_id, name="scope_id")
        data = with_retry(
            lambda: invoke_operation(
                self._http,
                self._ops.list_runs,
                path_params={"id": self._scope_id},
                query=aip_list_params(page_size, page_token),
            ),
            self._config.max_retries,
        )
        return build_aip_page_mapped(
            data,
            "runs",
            _map_run,
            lambda cur: self._list_runs_page(page_size, cur),
        )

    def get_run(self, run_id: str) -> EvaluationRunWithResults:
        validate_id(self._scope_id, name="scope_id")
        validate_id(run_id, name="run_id")
        data = with_retry(
            lambda: invoke_operation(
                self._http,
                self._ops.get_run,
                path_params={"id": self._scope_id, "runId": run_id},
            ),
            self._config.max_retries,
        )
        return EvaluationRunWithResults.model_validate(data)
