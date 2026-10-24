# Auto-generated from the Modus API schema. Do not edit by hand.

from __future__ import annotations

from typing import Optional, Protocol, Union

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


class _Operations(Protocol):
    @property
    def get_config(self) -> str: ...

    @property
    def get_run(self) -> str: ...

    @property
    def list_runs(self) -> str: ...

    @property
    def trigger_run(self) -> str: ...

    @property
    def update_config(self) -> str: ...


class _ScopesEvaluationsResourceBase:
    """Generated base for the management ``scopes.evaluations`` resource."""

    def __init__(
        self,
        http: HttpClient,
        config: ModusConfig,
        scope_id: Union[int, str],
        ops: _Operations,
    ) -> None:
        self._http = http
        self._config = config
        self._scope_id = scope_id
        self._ops = ops

    def get_config(self) -> EvaluationConfig:
        """
        Get evaluation configuration.

        Returns the evaluation configuration for a scope, including judge settings, schedule
        cadence, and notification preferences.

        **Requires:** ``scopes:read``
        """
        validate_id(self._scope_id, name="scope_id")
        raw = with_retry(
            lambda: invoke_operation(
                self._http,
                self._ops.get_config,
                path_params={"id": self._scope_id},
            ),
            self._config.max_retries,
        )
        return EvaluationConfig.model_validate(raw)

    def update_config(self, update: UpdateEvaluationConfig) -> EvaluationConfig:
        """
        Update evaluation configuration.

        Updates the evaluation configuration for a scope. Changes to the schedule cadence are synced
        automatically.

        **Requires:** ``scopes:write``

        Args:
            update: Request body; see :class:`UpdateEvaluationConfig`.
        """
        validate_id(self._scope_id, name="scope_id")
        body = update.model_dump(by_alias=False, exclude_none=True)
        raw = with_retry(
            lambda: invoke_operation(
                self._http,
                self._ops.update_config,
                path_params={"id": self._scope_id},
                json_body=body,
            ),
            self._config.max_retries,
        )
        return EvaluationConfig.model_validate(raw)

    def trigger_run(self) -> TriggerEvaluationRunResponse:
        """
        Trigger evaluation run.

        Triggers a manual evaluation run for the scope. The run executes asynchronously.

        **Requires:** ``scopes:write``

        Returns:
            Evaluation run accepted and queued. The run executes asynchronously; poll ``GET
                /scopes/{id}/evaluations/runs/{runId}`` for status.
        """
        validate_id(self._scope_id, name="scope_id")
        raw = with_retry(
            lambda: invoke_operation(
                self._http,
                self._ops.trigger_run,
                path_params={"id": self._scope_id},
            ),
            self._config.max_retries,
        )
        return TriggerEvaluationRunResponse.model_validate(raw)

    def list_runs(
        self,
        *,
        page_size: int = 25,
        page_token: Optional[str] = None,
    ) -> Page[EvaluationRun]:
        """
        List evaluation runs.

        Returns a paginated list of evaluation runs for the scope, ordered by most recent first.

        **Requires:** ``scopes:read``

        Args:
            page_size: Items per page. Defaults to 25.

        Returns:
            A page of runs.
        """
        validate_page_size(page_size)
        return self._list_runs_page(page_size, page_token)

    def _list_runs_page(self, page_size: int, page_token: Optional[str]) -> Page[EvaluationRun]:
        validate_id(self._scope_id, name="scope_id")
        params = aip_list_params(page_size, page_token)
        data = with_retry(
            lambda: invoke_operation(
                self._http,
                self._ops.list_runs,
                path_params={"id": self._scope_id},
                query=params,
            ),
            self._config.max_retries,
        )
        return build_aip_page_mapped(
            data,
            "runs",
            EvaluationRun.model_validate,
            lambda cur: self._list_runs_page(page_size, cur),
        )

    def get_run(self, run_id: str) -> EvaluationRunWithResults:
        """
        Get evaluation run.

        Returns details of an evaluation run including all per-case results.

        **Requires:** ``scopes:read``

        Args:
            run_id: Run ID.
        """
        validate_id(self._scope_id, name="scope_id")
        validate_id(run_id, name="run_id")
        raw = with_retry(
            lambda: invoke_operation(
                self._http,
                self._ops.get_run,
                path_params={"id": self._scope_id, "runId": run_id},
            ),
            self._config.max_retries,
        )
        return EvaluationRunWithResults.model_validate(raw)
