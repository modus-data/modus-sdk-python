"""Every ``"mode": "generated"`` exposure in ``sdk-surface.json`` is wired by a generated base.

The method must be inherited rather than hand-written on the public class, and the call must
reach the HTTP method, path and query parameters the OpenAPI spec declares for its operation.
"""

from __future__ import annotations

import importlib
import json
import re
import sys
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, AsyncIterator, Dict, List, Optional, Tuple

import httpx
import pytest
import respx
from modus import AsyncModus, Modus
from modus._generated.operations import OPERATIONS
from modus.management import AsyncModusManagement, ModusManagement

from .test_sdk_surface import _ASYNC_GAPS

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "scripts"))
from emit_sdk_resources import (  # noqa: E402
    _QUERY_ARG_TYPES,
    DEFAULT_SPEC,
    _spec_docs,
)

_CLIENTS_DIR = Path(__file__).resolve().parents[4]
_SURFACE = json.loads((_CLIENTS_DIR / "sdk-surface.json").read_text())

BASE = "https://api.modus.com"
API_KEY = "modus_test_key_abc123"
BOUND_ID = "1"
PATH_ARG = "p-1"

# The value a query argument takes, per OpenAPI scalar; one per key of ``_QUERY_ARG_TYPES``.
_QUERY_SAMPLES: Dict[str, Any] = {"string": "q", "integer": 7, "number": 1.5, "boolean": True}

# Resolved parameter schemas per operation, from the same derivation the emitter uses.
_SPEC_DOCS = _spec_docs(json.loads(DEFAULT_SPEC.read_text()))


def _query_sample(operation_id: str, name: str) -> Any:
    """The argument a query parameter is called with, chosen by the scalar the spec gives it."""
    schema = _SPEC_DOCS.get(operation_id, {}).get("schemas", {}).get(name) or {}
    sample = _QUERY_SAMPLES.get(schema.get("type"))
    if sample is None:
        raise AssertionError(
            f'{operation_id}: no wire sample for query parameter "{name}" ({schema!r})'
        )
    return sample


def _wire_value(operation_id: str, name: str) -> str:
    """The query string a sampled argument must serialise to."""
    sample = _query_sample(operation_id, name)
    if isinstance(sample, bool):
        return "true" if sample else "false"
    return str(sample)

# Minimal valid payloads for the body and return types a generated exposure names. A new
# generated type without an entry fails ``test_every_generated_type_has_a_sample``.
_SAMPLES: Dict[str, Dict[str, Any]] = {
    "Conversation": {
        "threadId": "thread-1", "scopeId": 0, "messages": [],
        "createdAt": "2026-01-01T00:00:00Z", "updatedAt": "2026-01-01T00:00:00Z",
    },
    'Dashboard': {'id': 'dash-1',
     'contextItemId': 'ci-1',
     'title': 'Revenue',
     'description': '',
     'access': {'visibility': 'private',
                'groupPermissions': {},
                'sharedWith': [{'email': 'ana@example.com',
                                'userId': 'user_2',
                                'permission': 'use'}],
                'ownerUserId': 'user_1',
                'ownerEmail': 'owner@example.com'},
     'definition': {'tiles': [{'id': 'tile-1',
                               'title': 'Revenue',
                               'kind': 'kpi',
                               'connectionId': 'conn-1',
                               'sql': 'select sum(amount) from orders',
                               'config': {}}],
                    'filters': [{'id': 'region',
                                 'label': 'Region',
                                 'type': 'string_list',
                                 'required': True,
                                 'quotation': 'single',
                                 'defaultValue': ['EMEA']}],
                    'layout': {'elements': {'tile-1': {'x': 0, 'y': 0, 'w': 4, 'h': 2}}}},
     'view': 'draft',
     'selectedVersion': {'id': None,
                         'versionNumber': None,
                         'createdByUserId': 'user_1',
                         'createdAt': '2026-09-16T10:00:00.000Z',
                         'access': {'visibility': 'private',
                                    'groupPermissions': {},
                                    'sharedWith': [{'email': 'ana@example.com',
                                                    'userId': 'user_2',
                                                    'permission': 'use'}],
                                    'ownerUserId': 'user_1',
                                    'ownerEmail': 'owner@example.com'}},
     'draftRevision': 4,
     'activeVersionId': None,
     'updatedByUserId': 'user_1',
     'createdAt': '2026-09-16T10:00:00.000Z',
     'updatedAt': '2026-09-16T10:05:00.000Z',
     'pendingOwnershipTransfer': None,
     'canUse': True,
     'canManage': True},
    'DashboardElementsList': {'dashboardId': 'dash-1', 'draftRevision': 3, 'elements': []},
    'DashboardElementResult': {'dashboardId': 'dash-1',
     'draftRevision': 3,
     'element': {'id': 'tile-1',
                 'kind': 'kpi',
                 'title': 'Revenue',
                 'layout': {'x': 0, 'y': 0, 'w': 4, 'h': 2},
                 'connectionId': 'conn-1',
                 'sql': 'select sum(amount) from orders',
                 'format': None}},
    'DashboardVersion': {'uid': 'v-1',
     'dashboardUid': 'dash-1',
     'versionNumber': 1,
     'kind': 'published',
     'title': 'Revenue',
     'description': '',
     'access': {'visibility': 'private',
                'groupPermissions': {},
                'sharedWith': [{'email': 'ana@example.com',
                                'userId': 'user_2',
                                'permission': 'use'}],
                'ownerUserId': 'user_1',
                'ownerEmail': 'owner@example.com'},
     'definition': {},
     'createdByUserId': 'user_1',
     'createdAt': '2026-09-16T10:00:00.000Z'},
    'DashboardDraftSnapshot': {'uid': 'snap-1', 'createdByUserId': 'user_1', 'createdAt': '2026-09-16T10:00:00.000Z'},
    'FileUpload': {'uploadId': 'up-1', 'status': 'processing'},
    "Workflow": {
        "id": 5, "slug": "weekly-report", "name": "Weekly report",
        "status": "active", "type": "task", "description": None,
        "orgUuid": "org-xyz", "hasUnpublishedChanges": False, "isEnabled": True,
        "activeVariationId": "var-1", "draftVariationId": None,
        "accessConfig": {
            "visibility": "shared",
            "groupPermissions": {"__everyone__": {"use": True, "manage": True}},
            "guardrails": [], "sharedWith": [],
        },
        "createdAt": "2026-01-01T00:00:00Z", "updatedAt": "2026-01-01T00:00:00Z",
        "deletedAt": None, "canManage": True, "canUse": True, "manageDenial": None,
    },
    "AgentInterface": {
        "id": "int_1", "agentId": 42, "type": "mcp", "name": "Internal", "config": {},
        "createdAt": "2026-01-01T00:00:00Z", "updatedAt": "2026-01-01T00:00:00Z",
    },
    'ScopeInterface': {'id': 'if-1', 'scopeId': 1, 'type': 'slack', 'name': 'Slack', 'config': {'accessMode': 'all'}, 'createdAt': '2026-01-01T00:00:00Z', 'updatedAt': '2026-01-01T00:00:00Z'},
    'Supervision': {'supervisorAgentId': 1, 'subordinateAgentIds': [2]},
    'SetSupervisionRequest': {'subordinateAgentIds': [2]},
    'EvaluationConfig': {'enabled': False, 'notifications': {'recipients': [], 'channels': {'email': False}}},
    'UpdateEvaluationConfig': {'enabled': True},
    'TriggerEvaluationRunResponse': {'runId': 'run-1'},
    'EvaluationRunWithResults': {'id': 'run-1', 'skillId': 1, 'trigger': 'manual', 'status': 'completed', 'startedAt': '2026-01-01T00:00:00Z', 'totalCases': 0, 'passedCases': 0, 'failedCases': 0, 'isRegression': False, 'results': []},
    "Scope": {'id': 1,
     'slug': 'test-skill',
     'name': 'Test Skill',
     'status': 'draft',
     'description': None,
     'orgUuid': 'org-xyz',
     'hasUnpublishedChanges': True,
     'activeVariationId': None,
     'draftVariationId': 'var-new',
     'accessConfig': {'visibility': 'shared',
                      'groupPermissions': {'__everyone__': {'use': True, 'manage': True}},
                      'guardrails': [],
                      'sharedWith': []},
     'createdAt': '2026-01-01T00:00:00Z',
     'updatedAt': '2026-01-01T00:00:00Z',
     'deletedAt': None,
     'canManage': True,
     'canUse': True,
     'manageDenial': None},
    "Memory": {"id": "mem_01", "memory": "User prefers bullet points."},
    "MemorySearchRequest": {"query": "revenue preferences"},
    "MemorySearchResult": {"memories": []},
    "MemoryUpdate": {"memory": "Updated text."},
    "UsageUsersReport": {"users": []},
}


def _snake(name: str) -> str:
    return re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", name).lower()


class Case:
    """One generated exposure, with the operation metadata the registry carries for it."""

    def __init__(self, operation_id: str, exposure: dict, pagination: Optional[dict]) -> None:
        self.operation_id = operation_id
        self.exposure = exposure
        self.pagination = pagination
        self.bind: Dict[str, str] = exposure.get("bind", {})
        self.query: List[str] = [
            entry if isinstance(entry, str) else entry["name"]
            for entry in exposure.get("query", [])
        ]
        self.method = exposure.get("pyMethod") or _snake(exposure["method"])
        self.label = (
            f"{operation_id}->{exposure['surface']}."
            f"{'.'.join(exposure['resource'])}.{self.method}"
        )

    @property
    def spec(self) -> dict:
        return OPERATIONS[self.operation_id]

    @property
    def positional_path_params(self) -> List[str]:
        return [name for name in self.spec["path_params"] if name not in self.bind]

    @property
    def expected_path(self) -> str:
        path = self.spec["path"]
        for name in self.spec["path_params"]:
            path = path.replace(f"{{{name}}}", BOUND_ID if name in self.bind else PATH_ARG)
        return path

    def response_body(self) -> Dict[str, Any]:
        if self.pagination:
            return {self.pagination["items"]: [], "nextPageToken": ""}
        returns = self.exposure.get("returns")
        value = _SAMPLES[returns] if returns else {}
        return {self.exposure["unwrap"]: [value]} if self.exposure.get("unwrap") else value

    @property
    def filter_kwargs(self) -> Dict[str, Any]:
        return {_snake(name): _query_sample(self.operation_id, name) for name in self.query}

    def call_args(self) -> Tuple[List[Any], Dict[str, Any]]:
        if self.pagination:
            return [], self.filter_kwargs
        args: List[Any] = [PATH_ARG for _ in self.positional_path_params]
        body = self.exposure.get("body")
        if body:
            args.append(_model(body["type"]).model_validate(_SAMPLES[body["type"]]))
        return args, self.filter_kwargs


def _model(type_name: str) -> Any:
    module = importlib.import_module(_SURFACE["types"][type_name]["py"])
    return getattr(module, _SURFACE["types"][type_name].get("pyName", type_name))


def _cases() -> List[Case]:
    return [
        Case(operation_id, exposure, operation.get("pagination"))
        for operation_id, operation in _SURFACE["operations"].items()
        if operation["mode"] == "generated"
        for exposure in operation.get("exposures", [])
    ]


CASES = _cases()
PAGINATED = [case for case in CASES if case.pagination]


def _params(cases: List[Case]) -> List[Any]:
    return [
        pytest.param(case, is_async, id=f"{case.label}-{'async' if is_async else 'sync'}")
        for case in cases
        for is_async in (False, True)
        if not is_async or case.operation_id not in _ASYNC_GAPS
    ]


@asynccontextmanager
async def _client(surface: str, is_async: bool) -> AsyncIterator[Any]:
    if is_async:
        cls = AsyncModus if surface == "consumption" else AsyncModusManagement
        async with cls(api_key=API_KEY, base_url=BASE) as client:  # type: ignore[operator]
            yield client
        return
    client = (Modus if surface == "consumption" else ModusManagement)(
        api_key=API_KEY, base_url=BASE
    )
    try:
        yield client
    finally:
        client.close()


def _resource(root: Any, case: Case) -> Any:
    target = root
    last = len(case.exposure["resource"]) - 1
    for index, name in enumerate(case.exposure["resource"]):
        target = getattr(target, _snake(name))
        if case.bind and index == last:
            target = target(BOUND_ID)
    return target


async def _await_if(value: Any, is_async: bool) -> Any:
    return await value if is_async else value


def test_covers_at_least_one_generated_exposure() -> None:
    assert CASES, 'sdk-surface.json has no "mode": "generated" exposure'


def test_every_query_scalar_the_emitter_accepts_has_a_wire_sample() -> None:
    missing = sorted(set(_QUERY_ARG_TYPES) - set(_QUERY_SAMPLES))
    assert not missing, f"Add a query sample for: {missing}"


def test_a_query_argument_is_sampled_from_the_spec_scalar() -> None:
    assert _query_sample("ConnectionsController_list", "type") == "q"
    assert _query_sample("ConnectionsController_list", "pageSize") == 1.5
    # A $ref parameter schema resolves before the scalar is read.
    assert _query_sample("DashboardsController_list", "view") == "q"


def test_every_generated_type_has_a_sample() -> None:
    needed = {
        name
        for case in CASES
        for name in ((case.exposure.get("body") or {}).get("type"), case.exposure.get("returns"))
        if name and not (case.pagination and name == case.exposure.get("returns"))
    }
    assert not needed - set(_SAMPLES), f"Add a sample payload for: {sorted(needed - set(_SAMPLES))}"


@pytest.mark.parametrize(("case", "is_async"), _params(CASES))
async def test_generated_method_is_inherited(case: Case, is_async: bool) -> None:
    async with _client(case.exposure["surface"], is_async) as client:
        resource = _resource(client, case)
        assert case.method not in type(resource).__dict__, (
            f"{case.label}: {type(resource).__name__} declares {case.method} itself; a generated "
            "exposure must be inherited from its generated base"
        )


@pytest.mark.parametrize(("case", "is_async"), _params(CASES))
async def test_generated_method_calls_the_spec_operation(case: Case, is_async: bool) -> None:
    async with _client(case.exposure["surface"], is_async) as client:
        with respx.mock(base_url=BASE, assert_all_called=False) as router:
            route = router.route().mock(
                return_value=httpx.Response(200, json=case.response_body())
            )
            args, kwargs = case.call_args()
            await _await_if(getattr(_resource(client, case), case.method)(*args, **kwargs), is_async)

    request = route.calls[0].request
    assert request.method == case.spec["method"]
    assert request.url.path == case.expected_path
    if case.pagination:
        assert not {"limit", "cursor"} & set(request.url.params)
        assert request.url.params["pageSize"] == str(case.exposure.get("pageSize", {}).get("default", 25))
    unexpected = sorted(set(request.url.params) - set(case.spec["query_params"]))
    assert not unexpected, f"{case.label}: query keys not in the spec: {unexpected}"
    for name in case.query:
        assert request.url.params.get(name) == _wire_value(case.operation_id, name), (
            f"{case.label}: {name} not forwarded"
        )
    if case.exposure.get("emptyBody"):
        assert json.loads(request.read()) == {}
    body = case.exposure.get("body")
    if body:
        sent = json.loads(request.read())
        assert sent == _SAMPLES[body["type"]], f"{case.label}: body not forwarded"


@pytest.mark.parametrize(("case", "is_async"), _params(PAGINATED))
async def test_paginated_method_keeps_every_filter_on_page_two(case: Case, is_async: bool) -> None:
    items = case.pagination["items"]  # type: ignore[index]
    async with _client(case.exposure["surface"], is_async) as client:
        with respx.mock(base_url=BASE, assert_all_called=False) as router:
            route = router.route().mock(
                side_effect=[
                    httpx.Response(200, json={items: [], "nextPageToken": "tok-2"}),
                    httpx.Response(200, json={items: [], "nextPageToken": ""}),
                ]
            )
            page = await _await_if(
                getattr(_resource(client, case), case.method)(**case.filter_kwargs),
                is_async,
            )
            await _await_if(page.get_next_page(), is_async)

    for index, where in ((0, "page 1"), (1, "page 2")):
        params = route.calls[index].request.url.params
        for name in case.query:
            assert params.get(name) == _wire_value(case.operation_id, name), (
                f"{case.label}: {name} missing on {where}"
            )
    assert route.calls[1].request.url.params["pageToken"] == "tok-2"


@pytest.mark.parametrize(("case", "is_async"), _params(PAGINATED))
async def test_paginated_method_omits_unset_filters(case: Case, is_async: bool) -> None:
    items = case.pagination["items"]  # type: ignore[index]
    async with _client(case.exposure["surface"], is_async) as client:
        with respx.mock(base_url=BASE, assert_all_called=False) as router:
            route = router.route().mock(
                return_value=httpx.Response(200, json={items: [], "nextPageToken": ""})
            )
            await _await_if(getattr(_resource(client, case), case.method)(), is_async)

    params = route.calls[0].request.url.params
    for name in case.query:
        assert name not in params, f"{case.label}: {name} sent while unset"
    assert params["pageSize"] == str(case.exposure.get("pageSize", {}).get("default", 25))
