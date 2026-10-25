"""Scheduled and manual skill evaluations for a scope."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Union
from uuid import uuid4

from modus._config import ModusConfig
from modus._generated.models import (
    EvaluationCaseDto,
    EvaluationCaseInputDto,
    UpdateEvaluationCaseDto,
)
from modus._generated.resources.management.scopes.evaluations import (
    _AsyncScopesEvaluationsResourceBase,
    _ScopesEvaluationsResourceBase,
)
from modus._http import AsyncHttpClient, HttpClient
from modus._openapi_invoke import invoke_operation, invoke_operation_async
from modus._retry import async_with_retry, with_retry
from modus._validation import validate_id


@dataclass(frozen=True)
class ScopeEvaluationsOperations:
    get_config: str
    update_config: str
    trigger_run: str
    list_runs: str
    get_run: str
    add_case: str
    update_case: str
    delete_case: str


SCOPE_EVALUATION_OPERATIONS = ScopeEvaluationsOperations(
    get_config="EvaluationsController_getConfig",
    update_config="EvaluationsController_updateConfig",
    trigger_run="EvaluationsController_triggerRun",
    list_runs="EvaluationsController_listRuns",
    get_run="EvaluationsController_getRun",
    add_case="ScopesController_addEvaluationCase",
    update_case="ScopesController_updateEvaluationCase",
    delete_case="ScopesController_deleteEvaluationCase",
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
        self._ops: ScopeEvaluationsOperations = ops

    def add_case(
        self,
        *,
        task: str,
        expected_output: str,
        id: Optional[str] = None,
    ) -> EvaluationCaseDto:
        """Add one evaluation case and return the stored case.

        Args:
            task: What the scope should do for this case. An empty string is allowed.
            expected_output: What a correct result looks like. An empty string is allowed.
            id: Stable id. Omit it and the client assigns one before the request,
                so a retry sends the same id.

        Returns:
            The stored evaluation case, including its id.

        Raises:
            ConflictError: An evaluation case with this id already exists.
                A retry after the case was stored returns this error.
                An identical body is not treated as success.
            AuthenticationError: Invalid or missing API key.

        Example:
            >>> case = mgmt.scopes.evaluations(42).add_case(
            ...     task="Summarize last quarter's revenue",
            ...     expected_output="A one-paragraph summary with the total",
            ... )
            >>> case.id
        """
        validate_id(self._scope_id, name="scope_id")
        case_id = id if id is not None else str(uuid4())
        validate_id(case_id, name="id")
        body = EvaluationCaseInputDto(task=task, expected_output=expected_output, id=case_id)
        data = with_retry(
            lambda: invoke_operation(
                self._http,
                self._ops.add_case,
                path_params={"id": self._scope_id},
                json_body=body.model_dump(by_alias=True, exclude_none=True),
            ),
            self._config.max_retries,
        )
        return EvaluationCaseDto.model_validate(data)

    def update_case(
        self,
        case_id: str,
        *,
        task: Optional[str] = None,
        expected_output: Optional[str] = None,
    ) -> EvaluationCaseDto:
        """Change the task, the expected output, or both, for one evaluation case.

        Args:
            case_id: Id of the case to change.
            task: Replacement for what the scope should do. Omit to leave it unchanged.
            expected_output: Replacement for a correct result. Omit to leave it unchanged.

        Returns:
            The evaluation case after the change.

        Raises:
            NotFoundError: No evaluation case has this id.
            AuthenticationError: Invalid or missing API key.

        Example:
            >>> case = mgmt.scopes.evaluations(42).update_case(
            ...     "CASE_ID", task="Summarize revenue in two sentences"
            ... )
            >>> case.task
        """
        validate_id(self._scope_id, name="scope_id")
        validate_id(case_id, name="case_id")
        body = UpdateEvaluationCaseDto(task=task, expected_output=expected_output)
        data = with_retry(
            lambda: invoke_operation(
                self._http,
                self._ops.update_case,
                path_params={"id": self._scope_id, "caseId": case_id},
                json_body=body.model_dump(by_alias=True, exclude_none=True),
            ),
            self._config.max_retries,
        )
        return EvaluationCaseDto.model_validate(data)

    def delete_case(self, case_id: str) -> None:
        """Remove one evaluation case. The other cases stay as they are.

        Args:
            case_id: Id of the case to remove.

        Raises:
            NotFoundError: No evaluation case has this id.
            AuthenticationError: Invalid or missing API key.

        Example:
            >>> mgmt.scopes.evaluations(42).delete_case("CASE_ID")
        """
        validate_id(self._scope_id, name="scope_id")
        validate_id(case_id, name="case_id")
        with_retry(
            lambda: invoke_operation(
                self._http,
                self._ops.delete_case,
                path_params={"id": self._scope_id, "caseId": case_id},
            ),
            self._config.max_retries,
        )


class AsyncScopeEvaluationsResource(_AsyncScopesEvaluationsResourceBase):
    def __init__(
        self,
        http: AsyncHttpClient,
        config: ModusConfig,
        scope_id: Union[int, str],
        ops: ScopeEvaluationsOperations = SCOPE_EVALUATION_OPERATIONS,
    ) -> None:
        super().__init__(http, config, scope_id, ops)
        self._ops: ScopeEvaluationsOperations = ops

    async def add_case(
        self,
        *,
        task: str,
        expected_output: str,
        id: Optional[str] = None,
    ) -> EvaluationCaseDto:
        """Add one evaluation case and return the stored case.

        Args:
            task: What the scope should do for this case. An empty string is allowed.
            expected_output: What a correct result looks like. An empty string is allowed.
            id: Stable id. Omit it and the client assigns one before the request,
                so a retry sends the same id.

        Returns:
            The stored evaluation case, including its id.

        Raises:
            ConflictError: An evaluation case with this id already exists.
                A retry after the case was stored returns this error.
                An identical body is not treated as success.
            AuthenticationError: Invalid or missing API key.

        Example:
            >>> case = await mgmt.scopes.evaluations(42).add_case(
            ...     task="Summarize last quarter's revenue",
            ...     expected_output="A one-paragraph summary with the total",
            ... )
            >>> case.id
        """
        validate_id(self._scope_id, name="scope_id")
        case_id = id if id is not None else str(uuid4())
        validate_id(case_id, name="id")
        body = EvaluationCaseInputDto(task=task, expected_output=expected_output, id=case_id)
        data = await async_with_retry(
            lambda: invoke_operation_async(
                self._http,
                self._ops.add_case,
                path_params={"id": self._scope_id},
                json_body=body.model_dump(by_alias=True, exclude_none=True),
            ),
            self._config.max_retries,
        )
        return EvaluationCaseDto.model_validate(data)

    async def update_case(
        self,
        case_id: str,
        *,
        task: Optional[str] = None,
        expected_output: Optional[str] = None,
    ) -> EvaluationCaseDto:
        """Change the task, the expected output, or both, for one evaluation case.

        Args:
            case_id: Id of the case to change.
            task: Replacement for what the scope should do. Omit to leave it unchanged.
            expected_output: Replacement for a correct result. Omit to leave it unchanged.

        Returns:
            The evaluation case after the change.

        Raises:
            NotFoundError: No evaluation case has this id.
            AuthenticationError: Invalid or missing API key.

        Example:
            >>> case = await mgmt.scopes.evaluations(42).update_case(
            ...     "CASE_ID", task="Summarize revenue in two sentences"
            ... )
            >>> case.task
        """
        validate_id(self._scope_id, name="scope_id")
        validate_id(case_id, name="case_id")
        body = UpdateEvaluationCaseDto(task=task, expected_output=expected_output)
        data = await async_with_retry(
            lambda: invoke_operation_async(
                self._http,
                self._ops.update_case,
                path_params={"id": self._scope_id, "caseId": case_id},
                json_body=body.model_dump(by_alias=True, exclude_none=True),
            ),
            self._config.max_retries,
        )
        return EvaluationCaseDto.model_validate(data)

    async def delete_case(self, case_id: str) -> None:
        """Remove one evaluation case. The other cases stay as they are.

        Args:
            case_id: Id of the case to remove.

        Raises:
            NotFoundError: No evaluation case has this id.
            AuthenticationError: Invalid or missing API key.

        Example:
            >>> await mgmt.scopes.evaluations(42).delete_case("CASE_ID")
        """
        validate_id(self._scope_id, name="scope_id")
        validate_id(case_id, name="case_id")
        await async_with_retry(
            lambda: invoke_operation_async(
                self._http,
                self._ops.delete_case,
                path_params={"id": self._scope_id, "caseId": case_id},
            ),
            self._config.max_retries,
        )
