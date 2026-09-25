"""Tests for mgmt.context.dashboards.* (documents, versions, access, elements and layout)."""

import json

import httpx
import pytest
import respx
from modus.management import AsyncModusManagement, ModusManagement
from modus.management.types.context_dashboards import (
    Dashboard,
    DashboardDraftSnapshot,
    DashboardElement,
    DashboardElementKind,
    DashboardElementLayout,
    DashboardElementPatch,
    DashboardElementResult,
    DashboardElementsList,
    DashboardGroupPermission,
    DashboardLayoutElement,
    DashboardPublishResult,
    DashboardSharedUser,
    DashboardSharePermission,
    DashboardVersion,
    DashboardView,
    DashboardVisibility,
)

BASE = "https://api.modus.com"
DASH = "dash-1"
ELEMENTS_URL = f"{BASE}/api/v1/context/dashboards/{DASH}/elements"
LAYOUT_URL = f"{BASE}/api/v1/context/dashboards/{DASH}/layout"
DASHBOARDS_URL = f"{BASE}/api/v1/context/dashboards"
DASH_URL = f"{DASHBOARDS_URL}/{DASH}"

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
def test_empty_document_ids_rejected_locally(bad):
    dashboards = _client().context.dashboards
    for call in (
        lambda: dashboards.get(bad),
        lambda: dashboards.update_draft(bad, expected_revision=1, definition={"tiles": [], "filters": []}),
        lambda: dashboards.publish(bad, expected_revision=1),
        lambda: dashboards.delete(bad),
        lambda: dashboards.list_versions(bad),
        lambda: dashboards.get_version(bad, "v1"),
        lambda: dashboards.restore_version(bad, "v1"),
        lambda: dashboards.list_draft_snapshots(bad),
        lambda: dashboards.update_access(bad, visibility="private", group_permissions={}, shared_with=[]),
        lambda: dashboards.request_ownership_transfer(bad, "user_2"),
        lambda: dashboards.accept_ownership_transfer(bad),
        lambda: dashboards.cancel_ownership_transfer(bad),
    ):
        with pytest.raises(ValueError, match="dashboard_id"):
            call()
    with pytest.raises(ValueError, match="version_id"):
        dashboards.get_version(DASH, bad)
    with pytest.raises(ValueError, match="version_id"):
        dashboards.restore_version(DASH, bad)
    with pytest.raises(ValueError, match="new_owner_user_id"):
        dashboards.request_ownership_transfer(DASH, bad)


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


# --- documents, versions, access and ownership --------------------------------

DEFINITION = DASHBOARD["definition"]
VERSION = {
    "uid": "v1",
    "dashboardUid": DASH,
    "versionNumber": 1,
    "kind": "published",
    "title": "Revenue",
    "description": "",
    "access": ACCESS,
    "definition": {"tiles": [{"id": "t1", "title": "T", "kind": "table"}], "filters": []},
    "createdByUserId": "user_1",
    "createdAt": "2026-09-16T10:00:00.000Z",
}
# Versions published before filters and element config existed store only tiles.
OLDER_VERSION = {
    **VERSION,
    "uid": "v0",
    "versionNumber": 0,
    "definition": {"tiles": [{"id": "t1", "title": "T", "kind": "table"}]},
}
SNAPSHOT = {"uid": "s1", "createdByUserId": "user_1", "createdAt": "2026-09-16T10:00:00.000Z"}
PENDING_TRANSFER = {
    **DASHBOARD,
    "pendingOwnershipTransfer": {
        "pendingOwnerUserId": "user_2",
        "pendingOwnerEmail": "ana@example.com",
        "requestedByUserId": "user_1",
        "requestedAt": "2026-09-16T10:00:00.000Z",
    },
}


@respx.mock
def test_dashboards_list_default_view_sends_no_query():
    route = respx.get(DASHBOARDS_URL).mock(
        return_value=httpx.Response(200, json={"dashboards": [DASHBOARD]})
    )
    result = _client().context.dashboards.list()
    assert [d.id for d in result] == [DASH]
    assert isinstance(result[0], Dashboard)
    assert "view" not in route.calls[0].request.url.params


@respx.mock
def test_dashboards_list_draft_view():
    route = respx.get(DASHBOARDS_URL).mock(
        return_value=httpx.Response(200, json={"dashboards": [DASHBOARD]})
    )
    result = _client().context.dashboards.list(view="draft")
    assert [d.id for d in result] == [DASH]
    assert route.calls[0].request.url.params["view"] == "draft"


@respx.mock
def test_dashboards_get_accepts_typed_view():
    route = respx.get(DASH_URL).mock(return_value=httpx.Response(200, json=DASHBOARD))
    result = _client().context.dashboards.get(DASH, view=DashboardView.draft)
    assert isinstance(result, Dashboard)
    assert result.draft_revision == 4
    assert route.calls[0].request.url.params["view"] == "draft"


@respx.mock
def test_dashboards_create_sends_only_given_fields():
    route = respx.post(DASHBOARDS_URL).mock(return_value=httpx.Response(201, json=DASHBOARD))
    result = _client().context.dashboards.create(title="Revenue", definition=DEFINITION)
    assert result.id == DASH
    assert json.loads(route.calls[0].request.read()) == {
        "title": "Revenue",
        "definition": DEFINITION,
    }


@respx.mock
def test_dashboards_create_with_description_and_access():
    route = respx.post(DASHBOARDS_URL).mock(return_value=httpx.Response(201, json=DASHBOARD))
    access = {"visibility": "shared", "groupPermissions": {"g1": {"use": True, "manage": False}}, "sharedWith": []}
    _client().context.dashboards.create(
        title="Revenue", definition=DEFINITION, description="Weekly", access=access
    )
    assert json.loads(route.calls[0].request.read()) == {
        "title": "Revenue",
        "definition": DEFINITION,
        "description": "Weekly",
        "access": access,
    }


@respx.mock
def test_dashboards_update_draft_sends_revision_and_definition():
    route = respx.patch(f"{DASH_URL}/draft").mock(return_value=httpx.Response(200, json=DASHBOARD))
    result = _client().context.dashboards.update_draft(
        DASH, expected_revision=3, definition=DEFINITION, title="Revenue v2"
    )
    assert result.draft_revision == 4
    assert json.loads(route.calls[0].request.read()) == {
        "expectedRevision": 3,
        "definition": DEFINITION,
        "title": "Revenue v2",
    }


@respx.mock
def test_dashboards_publish_returns_dashboard_and_version():
    route = respx.post(f"{DASH_URL}/publish").mock(
        return_value=httpx.Response(201, json={"dashboard": DASHBOARD, "version": VERSION})
    )
    result = _client().context.dashboards.publish(DASH, expected_revision=3)
    assert isinstance(result, DashboardPublishResult)
    assert result.version.kind == "published" and result.dashboard.id == DASH
    assert json.loads(route.calls[0].request.read()) == {"expectedRevision": 3}


@respx.mock
def test_dashboards_publish_accepts_older_version_definition():
    respx.post(f"{DASH_URL}/publish").mock(
        return_value=httpx.Response(201, json={"dashboard": DASHBOARD, "version": OLDER_VERSION})
    )
    result = _client().context.dashboards.publish(DASH, expected_revision=3)
    assert "filters" not in result.version.definition


@respx.mock
def test_dashboards_list_versions_accepts_older_definitions():
    respx.get(f"{DASH_URL}/versions").mock(
        return_value=httpx.Response(200, json={"versions": [VERSION, OLDER_VERSION]})
    )
    versions = _client().context.dashboards.list_versions(DASH)
    assert all(isinstance(v, DashboardVersion) for v in versions)
    assert versions[1].definition == OLDER_VERSION["definition"]
    assert versions[0].version_number == 1


@respx.mock
def test_dashboards_get_version_and_restore_version():
    get_route = respx.get(f"{DASH_URL}/versions/v1").mock(
        return_value=httpx.Response(200, json={**DASHBOARD, "view": "active"})
    )
    restore_route = respx.post(f"{DASH_URL}/versions/v1/restore").mock(
        return_value=httpx.Response(201, json=DASHBOARD)
    )
    dashboards = _client().context.dashboards
    assert dashboards.get_version(DASH, "v1").view == DashboardView.active
    assert dashboards.restore_version(DASH, "v1").view == DashboardView.draft
    assert get_route.called and restore_route.called
    assert restore_route.calls[0].request.content in (b"", b"null")


@respx.mock
def test_dashboards_list_draft_snapshots():
    respx.get(f"{DASH_URL}/draft-snapshots").mock(
        return_value=httpx.Response(200, json={"snapshots": [SNAPSHOT]})
    )
    snapshots = _client().context.dashboards.list_draft_snapshots(DASH)
    assert isinstance(snapshots[0], DashboardDraftSnapshot)
    assert snapshots[0].uid == "s1"


@respx.mock
def test_dashboards_delete_is_204():
    route = respx.delete(DASH_URL).mock(return_value=httpx.Response(204))
    assert _client().context.dashboards.delete(DASH) is None
    assert route.called


@respx.mock
def test_dashboards_update_access_sends_whole_object():
    route = respx.patch(f"{DASH_URL}/access").mock(return_value=httpx.Response(200, json=DASHBOARD))
    _client().context.dashboards.update_access(
        DASH,
        visibility="private",
        group_permissions={},
        shared_with=[{"email": "a@b.c", "permission": "use"}],
    )
    assert json.loads(route.calls[0].request.read()) == {
        "visibility": "private",
        "groupPermissions": {},
        "sharedWith": [{"email": "a@b.c", "permission": "use"}],
    }


@respx.mock
def test_dashboards_update_access_accepts_typed_values():
    route = respx.patch(f"{DASH_URL}/access").mock(return_value=httpx.Response(200, json=DASHBOARD))
    _client().context.dashboards.update_access(
        DASH,
        visibility=DashboardVisibility.shared,
        group_permissions={"g1": DashboardGroupPermission(use=True, manage=False)},
        shared_with=[DashboardSharedUser(email="ana@example.com", permission=DashboardSharePermission.use)],
    )
    assert json.loads(route.calls[0].request.read()) == {
        "visibility": "shared",
        "groupPermissions": {"g1": {"use": True, "manage": False}},
        "sharedWith": [{"email": "ana@example.com", "permission": "use"}],
    }


@respx.mock
def test_dashboards_ownership_request_and_accept():
    request_route = respx.post(f"{DASH_URL}/transfer-ownership").mock(
        return_value=httpx.Response(201, json=PENDING_TRANSFER)
    )
    accept_route = respx.post(f"{DASH_URL}/transfer-ownership/accept").mock(
        return_value=httpx.Response(201, json=DASHBOARD)
    )
    dashboards = _client().context.dashboards
    pending = dashboards.request_ownership_transfer(DASH, "user_2")
    assert pending.pending_ownership_transfer.pending_owner_user_id == "user_2"
    assert json.loads(request_route.calls[0].request.read()) == {"newOwnerUserId": "user_2"}
    assert dashboards.accept_ownership_transfer(DASH).id == DASH
    assert accept_route.called


@respx.mock
def test_dashboards_ownership_cancel():
    respx.delete(f"{DASH_URL}/transfer-ownership").mock(
        return_value=httpx.Response(200, json=DASHBOARD)
    )
    result = _client().context.dashboards.cancel_ownership_transfer(DASH)
    assert isinstance(result, Dashboard)
    assert result.id == DASH


@pytest.mark.asyncio
@respx.mock
async def test_async_document_operations():
    list_route = respx.get(DASHBOARDS_URL).mock(
        return_value=httpx.Response(200, json={"dashboards": [DASHBOARD]})
    )
    respx.post(DASHBOARDS_URL).mock(return_value=httpx.Response(201, json=DASHBOARD))
    get_route = respx.get(DASH_URL).mock(return_value=httpx.Response(200, json=DASHBOARD))
    draft_route = respx.patch(f"{DASH_URL}/draft").mock(
        return_value=httpx.Response(200, json=DASHBOARD)
    )
    respx.post(f"{DASH_URL}/publish").mock(
        return_value=httpx.Response(201, json={"dashboard": DASHBOARD, "version": OLDER_VERSION})
    )
    delete_route = respx.delete(DASH_URL).mock(return_value=httpx.Response(204))
    respx.get(f"{DASH_URL}/versions").mock(
        return_value=httpx.Response(200, json={"versions": [OLDER_VERSION]})
    )
    respx.get(f"{DASH_URL}/versions/v0").mock(return_value=httpx.Response(200, json=DASHBOARD))
    respx.post(f"{DASH_URL}/versions/v0/restore").mock(
        return_value=httpx.Response(201, json=DASHBOARD)
    )
    respx.get(f"{DASH_URL}/draft-snapshots").mock(
        return_value=httpx.Response(200, json={"snapshots": [SNAPSHOT]})
    )
    access_route = respx.patch(f"{DASH_URL}/access").mock(
        return_value=httpx.Response(200, json=DASHBOARD)
    )
    transfer_route = respx.post(f"{DASH_URL}/transfer-ownership").mock(
        return_value=httpx.Response(201, json=PENDING_TRANSFER)
    )
    respx.post(f"{DASH_URL}/transfer-ownership/accept").mock(
        return_value=httpx.Response(201, json=DASHBOARD)
    )
    cancel_route = respx.delete(f"{DASH_URL}/transfer-ownership").mock(
        return_value=httpx.Response(200, json=DASHBOARD)
    )
    async with _async_client() as mgmt:
        dashboards = mgmt.context.dashboards
        listed = await dashboards.list(view="draft")
        created = await dashboards.create(title="Revenue", definition=DEFINITION)
        got = await dashboards.get(DASH, view="draft")
        updated = await dashboards.update_draft(DASH, expected_revision=3, definition=DEFINITION)
        published = await dashboards.publish(DASH, expected_revision=4)
        deleted = await dashboards.delete(DASH)
        versions = await dashboards.list_versions(DASH)
        version = await dashboards.get_version(DASH, "v0")
        restored = await dashboards.restore_version(DASH, "v0")
        snapshots = await dashboards.list_draft_snapshots(DASH)
        access = await dashboards.update_access(
            DASH, visibility="private", group_permissions={}, shared_with=[]
        )
        pending = await dashboards.request_ownership_transfer(DASH, "user_2")
        accepted = await dashboards.accept_ownership_transfer(DASH)
        cancelled = await dashboards.cancel_ownership_transfer(DASH)
    assert [d.id for d in listed] == [DASH]
    assert list_route.calls[0].request.url.params["view"] == "draft"
    assert get_route.calls[0].request.url.params["view"] == "draft"
    for result in (created, got, updated, version, restored, access, accepted, cancelled):
        assert isinstance(result, Dashboard)
    assert isinstance(published, DashboardPublishResult)
    assert published.version.definition == OLDER_VERSION["definition"]
    assert deleted is None and delete_route.called
    assert isinstance(versions[0], DashboardVersion)
    assert isinstance(snapshots[0], DashboardDraftSnapshot)
    assert pending.pending_ownership_transfer is not None
    assert cancel_route.called
    assert json.loads(draft_route.calls[0].request.read()) == {
        "expectedRevision": 3,
        "definition": DEFINITION,
    }
    assert json.loads(access_route.calls[0].request.read()) == {
        "visibility": "private",
        "groupPermissions": {},
        "sharedWith": [],
    }
    assert json.loads(transfer_route.calls[0].request.read()) == {"newOwnerUserId": "user_2"}
