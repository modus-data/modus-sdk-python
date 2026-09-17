"""Tests for mgmt.context.dashboards.* (draft elements and layout)."""

import json

import httpx
import pytest
import respx
from modus.management import AsyncModusManagement, ModusManagement
from modus.management.types.context_dashboards import (
    Dashboard,
    DashboardElement,
    DashboardElementKind,
    DashboardElementLayout,
    DashboardElementPatch,
    DashboardElementResult,
    DashboardElementsList,
    DashboardLayoutElement,
)

BASE = "https://api.modus.com"
DASH = "dash-1"
ELEMENTS_URL = f"{BASE}/api/v1/context/dashboards/{DASH}/elements"
LAYOUT_URL = f"{BASE}/api/v1/context/dashboards/{DASH}/layout"

# Response fixtures mirror what the service returns today (see the dashboards
# service response builders): summaries omit sqlReferences on tiles, element
# layout is null when no position is stored, raw filters report their storage
# type as filterType, and KPI tiles report a null format when none is set.
ACCESS = {
    "visibility": "private",
    "groupPermissions": {},
    "sharedWith": [{"email": "ana@example.com", "userId": "user_2", "permission": "use"}],
    "ownerUserId": "user_1",
    "ownerEmail": "owner@example.com",
}

TILE_SUMMARY = {
    "id": "tile-1",
    "kind": "kpi",
    "title": "Revenue",
    "layout": {"x": 0, "y": 0, "w": 4, "h": 2},
}
FILTER_SUMMARY = {
    "id": "region",
    "kind": "filter",
    "title": "Region",
    "layout": None,
    "sqlReferences": ["{{ region }}"],
}
RANGE_SUMMARY = {
    "id": "period",
    "kind": "filter",
    "title": "Period",
    "layout": {"x": 4, "y": 0, "w": 4, "h": 1},
    "sqlReferences": ["{{ period.start }}", "{{ period.end }}"],
}

KPI_ELEMENT = {
    "id": "tile-1",
    "kind": "kpi",
    "title": "Revenue",
    "layout": {"x": 0, "y": 0, "w": 4, "h": 2},
    "connectionId": "conn-1",
    "sql": "select sum(amount) from orders",
    "format": None,
}
CHART_ELEMENT = {
    "id": "tile-2",
    "kind": "chart",
    "title": "Sales",
    "layout": None,
    "connectionId": "",
    "sql": "",
    "chartConfig": None,
}
RAW_FILTER_ELEMENT = {
    "id": "region",
    "kind": "filter",
    "title": "Region",
    "filterType": "string_list",
    "required": True,
    "defaultValue": None,
    "sqlReferences": ["{{ region }}"],
    "layout": None,
}
RANGE_FILTER_ELEMENT = {
    "id": "period",
    "kind": "filter",
    "title": "Period",
    "filterType": "date_range",
    "required": False,
    "options": [],
    "allowMultiple": False,
    "quotation": "single",
    "defaultValue": {"start": "2026-01-01", "end": "2026-03-31"},
    "sqlReferences": ["{{ period.start }}", "{{ period.end }}"],
    "layout": {"x": 4, "y": 0, "w": 4, "h": 1},
}

DASHBOARD = {
    "id": DASH,
    "contextItemId": "ci-1",
    "title": "Revenue",
    "description": "",
    "access": ACCESS,
    "definition": {
        "tiles": [
            {
                "id": "tile-1",
                "title": "Revenue",
                "kind": "kpi",
                "connectionId": "conn-1",
                "sql": "select sum(amount) from orders",
                "config": {},
            }
        ],
        "filters": [
            {
                "id": "region",
                "label": "Region",
                "type": "string_list",
                "required": True,
                "quotation": "single",
                "defaultValue": ["EMEA"],
            }
        ],
        "layout": {"elements": {"tile-1": {"x": 0, "y": 0, "w": 4, "h": 2}}},
    },
    "view": "draft",
    "selectedVersion": {
        "id": None,
        "versionNumber": None,
        "createdByUserId": "user_1",
        "createdAt": "2026-09-16T10:00:00.000Z",
        "access": ACCESS,
    },
    "draftRevision": 4,
    "activeVersionId": None,
    "updatedByUserId": "user_1",
    "createdAt": "2026-09-16T10:00:00.000Z",
    "updatedAt": "2026-09-16T10:05:00.000Z",
    "pendingOwnershipTransfer": None,
    "canUse": True,
    "canManage": True,
}


def _client() -> ModusManagement:
    return ModusManagement(api_key="modus_test_key", base_url=BASE)


def _async_client() -> AsyncModusManagement:
    return AsyncModusManagement(api_key="modus_test_key", base_url=BASE)


def _element_result(element: dict, revision: int = 3) -> dict:
    return {"dashboardId": DASH, "draftRevision": revision, "element": element}


# --- response models -------------------------------------------------------


def test_models_validate_service_payloads():
    listed = DashboardElementsList.model_validate(
        {"dashboardId": DASH, "draftRevision": 3, "elements": [TILE_SUMMARY, FILTER_SUMMARY, RANGE_SUMMARY]}
    )
    assert listed.elements[1].layout is None
    assert listed.elements[0].sql_references is None

    for element in (KPI_ELEMENT, CHART_ELEMENT, RAW_FILTER_ELEMENT, RANGE_FILTER_ELEMENT):
        result = DashboardElementResult.model_validate(_element_result(element))
        assert isinstance(result.element, DashboardElement)

    dashboard = Dashboard.model_validate(DASHBOARD)
    assert dashboard.access.owner_email == "owner@example.com"
    assert dashboard.pending_ownership_transfer is None
    assert dashboard.definition.filters[0].type.value == "string_list"
    assert dashboard.selected_version.id is None


# --- sync ------------------------------------------------------------------


@respx.mock
def test_elements_list():
    respx.get(ELEMENTS_URL).mock(
        return_value=httpx.Response(
            200,
            json={"dashboardId": DASH, "draftRevision": 3, "elements": [TILE_SUMMARY, FILTER_SUMMARY]},
        )
    )
    result = _client().context.dashboards.elements(DASH).list()
    assert isinstance(result, DashboardElementsList)
    assert result.draft_revision == 3
    assert [e.id for e in result.elements] == ["tile-1", "region"]
    assert result.elements[0].kind == DashboardElementKind.kpi
    assert result.elements[1].sql_references == ["{{ region }}"]


@respx.mock
def test_elements_get_raw_filter_reports_storage_type():
    respx.get(f"{ELEMENTS_URL}/region").mock(
        return_value=httpx.Response(200, json=_element_result(RAW_FILTER_ELEMENT))
    )
    result = _client().context.dashboards.elements(DASH).get("region")
    assert isinstance(result, DashboardElementResult)
    assert result.element.filter_type == "string_list"
    assert result.element.default_value is None
    assert result.element.layout is None


@respx.mock
def test_elements_get_range_filter_default_value_object():
    respx.get(f"{ELEMENTS_URL}/period").mock(
        return_value=httpx.Response(200, json=_element_result(RANGE_FILTER_ELEMENT))
    )
    element = _client().context.dashboards.elements(DASH).get("period").element
    assert element.default_value == {"start": "2026-01-01", "end": "2026-03-31"}


@respx.mock
def test_elements_get_kpi_null_format():
    respx.get(f"{ELEMENTS_URL}/tile-1").mock(
        return_value=httpx.Response(200, json=_element_result(KPI_ELEMENT))
    )
    element = _client().context.dashboards.elements(DASH).get("tile-1").element
    assert element.format is None
    assert element.connection_id == "conn-1"


@respx.mock
def test_elements_get_url_encodes_element_id():
    route = respx.get(f"{ELEMENTS_URL}/a%2Fb").mock(
        return_value=httpx.Response(200, json=_element_result({**KPI_ELEMENT, "id": "a/b"}))
    )
    _client().context.dashboards.elements(DASH).get("a/b")
    assert route.called


@respx.mock
def test_elements_create_sends_body_from_plain_values():
    route = respx.post(ELEMENTS_URL).mock(
        return_value=httpx.Response(201, json=_element_result({**CHART_ELEMENT, "id": "new"}, 4))
    )
    result = _client().context.dashboards.elements(DASH).create(
        expected_revision=3,
        kind="chart",
        title="Sales",
        layout={"x": 0, "y": 2, "w": 6, "h": 4},
    )
    assert result.element.id == "new"
    assert result.draft_revision == 4
    body = json.loads(route.calls[0].request.read())
    assert body == {
        "expectedRevision": 3,
        "kind": "chart",
        "title": "Sales",
        "layout": {"x": 0, "y": 2, "w": 6, "h": 4},
    }


@respx.mock
def test_elements_create_accepts_typed_values():
    route = respx.post(ELEMENTS_URL).mock(
        return_value=httpx.Response(201, json=_element_result(RAW_FILTER_ELEMENT, 4))
    )
    _client().context.dashboards.elements(DASH).create(
        expected_revision=3,
        kind=DashboardElementKind.filter,
        title="Region",
        layout=DashboardElementLayout(x=0, y=6, w=3, h=1),
    )
    body = json.loads(route.calls[0].request.read())
    assert body == {
        "expectedRevision": 3,
        "kind": "filter",
        "title": "Region",
        "layout": {"x": 0, "y": 6, "w": 3, "h": 1},
    }


@respx.mock
def test_elements_update_returns_dashboard():
    route = respx.patch(f"{ELEMENTS_URL}/tile-1").mock(
        return_value=httpx.Response(200, json=DASHBOARD)
    )
    result = _client().context.dashboards.elements(DASH).update(
        "tile-1", expected_revision=3, patch={"title": "Regions"}
    )
    assert isinstance(result, Dashboard)
    assert result.draft_revision == 4
    body = json.loads(route.calls[0].request.read())
    assert body == {"expectedRevision": 3, "patch": {"title": "Regions"}}


@respx.mock
def test_elements_update_typed_patch_keeps_explicit_nulls():
    route = respx.patch(f"{ELEMENTS_URL}/region").mock(
        return_value=httpx.Response(200, json=DASHBOARD)
    )
    _client().context.dashboards.elements(DASH).update(
        "region",
        expected_revision=3,
        patch=DashboardElementPatch(allow_multiple=True, default_value=None),
    )
    body = json.loads(route.calls[0].request.read())
    assert body == {
        "expectedRevision": 3,
        "patch": {"allowMultiple": True, "defaultValue": None},
    }


CHART_CONFIG_WIRE = {
    "type": "bar",
    "labelColumn": "region",
    "datasets": [
        {"label": "Revenue", "valueColumn": "revenue", "backgroundColor": "#336699", "borderWidth": 2}
    ],
    "options": {"plugins": {"legend": {"display": False}}},
    "indexAxis": "y",
}


@respx.mock
def test_elements_update_typed_chart_config_keeps_chart_js_keys():
    route = respx.patch(f"{ELEMENTS_URL}/tile-2").mock(
        return_value=httpx.Response(200, json=DASHBOARD)
    )
    _client().context.dashboards.elements(DASH).update(
        "tile-2",
        expected_revision=3,
        patch=DashboardElementPatch(chart_config=CHART_CONFIG_WIRE),
    )
    body = json.loads(route.calls[0].request.read())
    assert body == {"expectedRevision": 3, "patch": {"chartConfig": CHART_CONFIG_WIRE}}


@respx.mock
def test_elements_update_dict_chart_config_keeps_chart_js_keys():
    route = respx.patch(f"{ELEMENTS_URL}/tile-2").mock(
        return_value=httpx.Response(200, json=DASHBOARD)
    )
    _client().context.dashboards.elements(DASH).update(
        "tile-2",
        expected_revision=3,
        patch={"chartConfig": CHART_CONFIG_WIRE},
    )
    body = json.loads(route.calls[0].request.read())
    assert body == {"expectedRevision": 3, "patch": {"chartConfig": CHART_CONFIG_WIRE}}


@respx.mock
def test_update_layout():
    route = respx.patch(LAYOUT_URL).mock(return_value=httpx.Response(200, json=DASHBOARD))
    result = _client().context.dashboards.update_layout(
        DASH,
        expected_revision=3,
        elements=[
            {"elementId": "tile-1", "layout": {"x": 0, "y": 0, "w": 12, "h": 2}},
            DashboardLayoutElement(
                element_id="region",
                layout=DashboardElementLayout(x=0, y=2, w=3, h=1),
            ),
        ],
    )
    assert isinstance(result, Dashboard)
    body = json.loads(route.calls[0].request.read())
    assert body == {
        "expectedRevision": 3,
        "elements": [
            {"elementId": "tile-1", "layout": {"x": 0, "y": 0, "w": 12, "h": 2}},
            {"elementId": "region", "layout": {"x": 0, "y": 2, "w": 3, "h": 1}},
        ],
    }


@pytest.mark.parametrize("bad", ["", "   "])
def test_empty_ids_rejected_locally(bad):
    dashboards = _client().context.dashboards
    with pytest.raises(ValueError, match="dashboard_id"):
        dashboards.elements(bad)
    with pytest.raises(ValueError, match="dashboard_id"):
        dashboards.update_layout(bad, expected_revision=1, elements=[])
    with pytest.raises(ValueError, match="element_id"):
        dashboards.elements(DASH).get(bad)
    with pytest.raises(ValueError, match="element_id"):
        dashboards.elements(DASH).update(bad, expected_revision=1, patch={"title": "x"})


# --- async -----------------------------------------------------------------


@pytest.mark.asyncio
@respx.mock
async def test_async_elements_list_and_get():
    respx.get(ELEMENTS_URL).mock(
        return_value=httpx.Response(
            200, json={"dashboardId": DASH, "draftRevision": 3, "elements": [RANGE_SUMMARY]}
        )
    )
    respx.get(f"{ELEMENTS_URL}/period").mock(
        return_value=httpx.Response(200, json=_element_result(RANGE_FILTER_ELEMENT))
    )
    async with _async_client() as mgmt:
        listed = await mgmt.context.dashboards.elements(DASH).list()
        got = await mgmt.context.dashboards.elements(DASH).get("period")
    assert isinstance(listed, DashboardElementsList)
    assert listed.elements[0].sql_references == ["{{ period.start }}", "{{ period.end }}"]
    assert isinstance(got, DashboardElementResult)
    assert got.element.filter_type == "date_range"


@pytest.mark.asyncio
@respx.mock
async def test_async_writes_send_bodies():
    create = respx.post(ELEMENTS_URL).mock(
        return_value=httpx.Response(201, json=_element_result(KPI_ELEMENT, 4))
    )
    update = respx.patch(f"{ELEMENTS_URL}/tile-1").mock(
        return_value=httpx.Response(200, json=DASHBOARD)
    )
    layout = respx.patch(LAYOUT_URL).mock(return_value=httpx.Response(200, json=DASHBOARD))
    async with _async_client() as mgmt:
        created = await mgmt.context.dashboards.elements(DASH).create(
            expected_revision=3,
            kind="kpi",
            title="Revenue",
            layout={"x": 0, "y": 0, "w": 4, "h": 2},
        )
        updated = await mgmt.context.dashboards.elements(DASH).update(
            "tile-1", expected_revision=4, patch={"format": "currency"}
        )
        laid_out = await mgmt.context.dashboards.update_layout(
            DASH,
            expected_revision=4,
            elements=[{"elementId": "tile-1", "layout": {"x": 2, "y": 0, "w": 4, "h": 2}}],
        )
    assert isinstance(created, DashboardElementResult)
    assert isinstance(updated, Dashboard)
    assert isinstance(laid_out, Dashboard)
    assert json.loads(create.calls[0].request.read()) == {
        "expectedRevision": 3,
        "kind": "kpi",
        "title": "Revenue",
        "layout": {"x": 0, "y": 0, "w": 4, "h": 2},
    }
    assert json.loads(update.calls[0].request.read()) == {
        "expectedRevision": 4,
        "patch": {"format": "currency"},
    }
    assert json.loads(layout.calls[0].request.read()) == {
        "expectedRevision": 4,
        "elements": [{"elementId": "tile-1", "layout": {"x": 2, "y": 0, "w": 4, "h": 2}}],
    }
