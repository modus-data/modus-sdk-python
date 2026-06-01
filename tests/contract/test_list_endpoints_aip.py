"""
Respx round-trip contract tests: SDK list methods vs AIP-158 request/response shapes.
"""
from __future__ import annotations

from typing import Union

import httpx
import pytest
import respx
from modus import Modus
from modus._exceptions import ModusError
from modus.management import ModusManagement
from modus.types.pagination import Page
from pydantic import ValidationError

from .conftest import TEST_BASE_URL
from .list_operations import (
    REJECTED_LIST_RESPONSE_BODY,
    SDK_AIP_LIST_OPERATIONS,
    ListOperationSpec,
    success_body,
    wrong_key_body,
)

FORBIDDEN_QUERY_PARAMS = frozenset({"limit", "cursor"})


def _client_for_spec(
    spec: ListOperationSpec,
    contract_client: Modus,
    contract_management_client: ModusManagement,
) -> Union[Modus, ModusManagement]:
    if spec.client_kind == "management":
        return contract_management_client
    return contract_client


@pytest.mark.parametrize(
    "spec",
    SDK_AIP_LIST_OPERATIONS,
    ids=lambda s: f"{s.operation_id}:{s.client_kind}",
)
@respx.mock
def test_list_success_parses_aip_response(
    spec: ListOperationSpec,
    contract_client: Modus,
    contract_management_client: ModusManagement,
) -> None:
    respx.get(f"{TEST_BASE_URL}{spec.mock_url_suffix}").mock(
        return_value=httpx.Response(200, json=success_body(spec))
    )
    client = _client_for_spec(spec, contract_client, contract_management_client)
    page = spec.invoke(client)
    assert isinstance(page, Page)
    assert len(page) == 1


@pytest.mark.parametrize(
    "spec",
    SDK_AIP_LIST_OPERATIONS,
    ids=lambda s: f"{s.operation_id}:{s.client_kind}",
)
@respx.mock
def test_list_rejects_non_aip_response_body(
    spec: ListOperationSpec,
    contract_client: Modus,
    contract_management_client: ModusManagement,
) -> None:
    respx.get(f"{TEST_BASE_URL}{spec.mock_url_suffix}").mock(
        return_value=httpx.Response(200, json=REJECTED_LIST_RESPONSE_BODY)
    )
    client = _client_for_spec(spec, contract_client, contract_management_client)
    if spec.bad_body_raises_pydantic:
        with pytest.raises(ValidationError):
            spec.invoke(client)
    else:
        with pytest.raises(ModusError):
            spec.invoke(client)


@pytest.mark.parametrize(
    "spec",
    SDK_AIP_LIST_OPERATIONS,
    ids=lambda s: f"{s.operation_id}:{s.client_kind}",
)
@respx.mock
def test_list_wrong_plural_key_fails(
    spec: ListOperationSpec,
    contract_client: Modus,
    contract_management_client: ModusManagement,
) -> None:
    respx.get(f"{TEST_BASE_URL}{spec.mock_url_suffix}").mock(
        return_value=httpx.Response(200, json=wrong_key_body(spec))
    )
    client = _client_for_spec(spec, contract_client, contract_management_client)
    if spec.bad_body_raises_pydantic:
        with pytest.raises(ValidationError):
            spec.invoke(client)
    else:
        with pytest.raises(ModusError):
            spec.invoke(client)


@pytest.mark.parametrize(
    "spec",
    SDK_AIP_LIST_OPERATIONS,
    ids=lambda s: f"{s.operation_id}:{s.client_kind}",
)
@respx.mock
def test_list_sends_aip_query_params_only(
    spec: ListOperationSpec,
    contract_client: Modus,
    contract_management_client: ModusManagement,
) -> None:
    route = respx.get(f"{TEST_BASE_URL}{spec.mock_url_suffix}").mock(
        return_value=httpx.Response(200, json=success_body(spec))
    )
    client = _client_for_spec(spec, contract_client, contract_management_client)
    spec.invoke(client)
    assert route.called
    params = route.calls[0].request.url.params
    assert params["pageSize"] == "25"
    assert params["pageToken"] == "tok_abc"
    assert not (set(params.keys()) & FORBIDDEN_QUERY_PARAMS), (
        f"{spec.operation_id}: must not send non-AIP pagination query params"
    )
