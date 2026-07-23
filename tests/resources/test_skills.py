"""Tests for client.scopes.list() and client.scopes.get()."""

import httpx
import pytest
import respx
from modus import NotFoundError
from modus.types.skills import Skill

BASE = "https://api.modus.com"


@respx.mock
def test_skills_list(client, sample_skill):
    respx.get(f"{BASE}/api/v1/scopes").mock(
        return_value=httpx.Response(200, json={"scopes": [sample_skill], "nextPageToken": None})
    )
    page = client.scopes.list()
    assert len(page) == 1
    skill = page.items[0]
    assert isinstance(skill, Skill)
    assert skill.id == 42
    assert skill.slug == "revenue-analysis"
    assert skill.status == "active"


@respx.mock
def test_skills_list_default_page_size_in_params(client):
    route = respx.get(f"{BASE}/api/v1/scopes").mock(
        return_value=httpx.Response(200, json={"scopes": [], "nextPageToken": None})
    )
    client.scopes.list()
    assert route.called
    assert route.calls[0].request.url.params["pageSize"] == "25"


@respx.mock
def test_skills_list_custom_page_size(client):
    route = respx.get(f"{BASE}/api/v1/scopes").mock(
        return_value=httpx.Response(200, json={"scopes": [], "nextPageToken": None})
    )
    client.scopes.list(page_size=5)
    assert route.calls[0].request.url.params["pageSize"] == "5"


@respx.mock
def test_skills_list_pagination(client, sample_skill):
    skill2 = {**sample_skill, "id": 43, "slug": "churn-analysis", "name": "Churn Analysis"}

    route = respx.get(f"{BASE}/api/v1/scopes").mock(side_effect=[
        httpx.Response(200, json={"scopes": [sample_skill], "nextPageToken": "tok_page_2"}),
        httpx.Response(200, json={"scopes": [skill2], "nextPageToken": None}),
    ])

    page = client.scopes.list()
    assert page.has_next_page() is True

    all_skills = list(page.auto_paging_iter())
    assert len(all_skills) == 2
    assert all_skills[0].id == 42
    assert all_skills[1].id == 43
    assert route.call_count == 2
    assert route.calls[1].request.url.params["pageToken"] == "tok_page_2"


@respx.mock
def test_skills_list_iter_current_page_only(client, sample_skill):
    respx.get(f"{BASE}/api/v1/scopes").mock(
        return_value=httpx.Response(
            200, json={"scopes": [sample_skill], "nextPageToken": "has_more"}
        )
    )
    page = client.scopes.list()
    # Iterating page should NOT trigger a second request
    items = list(page)
    assert len(items) == 1


@respx.mock
def test_skills_get(client, sample_skill):
    respx.get(f"{BASE}/api/v1/scopes/42").mock(
        return_value=httpx.Response(200, json=sample_skill)
    )
    skill = client.scopes.get(42)
    assert isinstance(skill, Skill)
    assert skill.id == 42
    assert skill.name == "Revenue Analysis"


@respx.mock
def test_skills_get_by_slug(client, sample_skill):
    respx.get(f"{BASE}/api/v1/scopes/revenue-analysis").mock(
        return_value=httpx.Response(200, json=sample_skill)
    )
    skill = client.scopes.get("revenue-analysis")
    assert skill.slug == "revenue-analysis"


@respx.mock
def test_skills_get_not_found(client):
    respx.get(f"{BASE}/api/v1/scopes/999").mock(
        return_value=httpx.Response(404, json={"message": "Skill not found"})
    )
    with pytest.raises(NotFoundError, match="Skill not found"):
        client.scopes.get(999)


@respx.mock
def test_skill_properties(client, sample_skill):
    respx.get(f"{BASE}/api/v1/scopes/42").mock(
        return_value=httpx.Response(200, json=sample_skill)
    )
    skill = client.scopes.get(42)
    assert skill.status == "active"


@respx.mock
def test_skills_get_url_encodes_slug(client, sample_skill):
    """Slugs with special characters must be percent-encoded in the URL path."""
    route = respx.get(f"{BASE}/api/v1/scopes/my%20skill%2Fname").mock(
        return_value=httpx.Response(200, json=sample_skill)
    )
    client.scopes.get("my skill/name")
    assert route.called
