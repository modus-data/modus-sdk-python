"""Tests for client.skills.list() and client.skills.get()."""

import httpx
import pytest
import respx
from modus import Modus, NotFoundError
from modus.types.skills import Skill

BASE = "https://api.modus.com"


@respx.mock
def test_skills_list(client, sample_skill):
    respx.get(f"{BASE}/api/v1/skills").mock(
        return_value=httpx.Response(200, json={"items": [sample_skill], "nextCursor": None})
    )
    page = client.skills.list()
    assert len(page) == 1
    skill = page.items[0]
    assert isinstance(skill, Skill)
    assert skill.id == 42
    assert skill.slug == "revenue-analysis"
    assert skill.status == "active"


@respx.mock
def test_skills_list_default_limit_in_params(client):
    route = respx.get(f"{BASE}/api/v1/skills").mock(
        return_value=httpx.Response(200, json={"items": [], "nextCursor": None})
    )
    client.skills.list()
    assert route.called
    assert route.calls[0].request.url.params["limit"] == "20"


@respx.mock
def test_skills_list_custom_limit(client):
    route = respx.get(f"{BASE}/api/v1/skills").mock(
        return_value=httpx.Response(200, json={"items": [], "nextCursor": None})
    )
    client.skills.list(limit=5)
    assert route.calls[0].request.url.params["limit"] == "5"


@respx.mock
def test_skills_list_pagination(client, sample_skill):
    skill2 = {**sample_skill, "id": 43, "slug": "churn-analysis", "name": "Churn Analysis"}

    respx.get(f"{BASE}/api/v1/skills").mock(side_effect=[
        httpx.Response(200, json={"items": [sample_skill], "nextCursor": "cursor_abc"}),
        httpx.Response(200, json={"items": [skill2], "nextCursor": None}),
    ])

    page = client.skills.list()
    assert page.has_next_page() is True

    all_skills = list(page.auto_paging_iter())
    assert len(all_skills) == 2
    assert all_skills[0].id == 42
    assert all_skills[1].id == 43


@respx.mock
def test_skills_list_iter_current_page_only(client, sample_skill):
    respx.get(f"{BASE}/api/v1/skills").mock(
        return_value=httpx.Response(
            200, json={"items": [sample_skill], "nextCursor": "has_more"}
        )
    )
    page = client.skills.list()
    # Iterating page should NOT trigger a second request
    items = list(page)
    assert len(items) == 1


@respx.mock
def test_skills_get(client, sample_skill):
    respx.get(f"{BASE}/api/v1/skills/42").mock(
        return_value=httpx.Response(200, json=sample_skill)
    )
    skill = client.skills.get(42)
    assert isinstance(skill, Skill)
    assert skill.id == 42
    assert skill.name == "Revenue Analysis"


@respx.mock
def test_skills_get_by_slug(client, sample_skill):
    respx.get(f"{BASE}/api/v1/skills/revenue-analysis").mock(
        return_value=httpx.Response(200, json=sample_skill)
    )
    skill = client.skills.get("revenue-analysis")
    assert skill.slug == "revenue-analysis"


@respx.mock
def test_skills_get_not_found(client):
    respx.get(f"{BASE}/api/v1/skills/999").mock(
        return_value=httpx.Response(404, json={"message": "Skill not found"})
    )
    with pytest.raises(NotFoundError, match="Skill not found"):
        client.skills.get(999)


@respx.mock
def test_skill_properties(client, sample_skill):
    respx.get(f"{BASE}/api/v1/skills/42").mock(
        return_value=httpx.Response(200, json=sample_skill)
    )
    skill = client.skills.get(42)
    assert skill.is_active is True
    assert skill.is_draft is False


@respx.mock
def test_skills_get_url_encodes_slug(client, sample_skill):
    """Slugs with special characters must be percent-encoded in the URL path."""
    route = respx.get(f"{BASE}/api/v1/skills/my%20skill%2Fname").mock(
        return_value=httpx.Response(200, json=sample_skill)
    )
    client.skills.get("my skill/name")
    assert route.called
