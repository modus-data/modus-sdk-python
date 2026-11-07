"""Numeric ids are ``int``: the spec declares them ``type: integer``.

Before, the spec said ``type: number``, so models typed ids as ``float``: they printed as
``34.0`` and mypy rejected the README's own ``client.scopes.get(first.id)``.
"""

from __future__ import annotations

import httpx
import respx
from modus import Modus
from mypy import api as mypy_api

BASE = "https://api.modus.com/api/v1"

_SCOPE = {
    "id": 34, "slug": "s", "name": "S", "status": "active", "description": None,
    "orgUuid": "org", "hasUnpublishedChanges": False, "activeVariationId": "v",
    "draftVariationId": None, "accessConfig": {"visibility": "shared", "groupPermissions": {},
    "guardrails": [], "sharedWith": []}, "createdAt": "2026-01-01T00:00:00Z",
    "updatedAt": "2026-01-01T00:00:00Z", "deletedAt": None,
    "canManage": True, "canUse": True, "manageDenial": None,
}


@respx.mock
def test_listed_scope_id_is_int_and_round_trips(client: Modus) -> None:
    respx.get(url__regex=rf"{BASE}/scopes(\?.*)?$").mock(
        return_value=httpx.Response(200, json={"scopes": [_SCOPE], "nextPageToken": None}))
    get = respx.get(f"{BASE}/scopes/34").mock(return_value=httpx.Response(200, json=_SCOPE))

    first = client.scopes.list().items[0]

    assert type(first.id) is int
    assert f"{first.id}" == "34"
    assert client.scopes.get(first.id).id == 34
    assert get.called


def test_readme_get_by_listed_id_typechecks_under_mypy_strict() -> None:
    snippet = (
        "from modus import Modus\n"
        "def first_scope_id(client: Modus) -> int:\n"
        "    first = client.scopes.list().items[0]\n"
        "    client.scopes.get(first.id)\n"
        "    return first.id\n"
    )
    stdout, stderr, status = mypy_api.run(
        ["--strict", "--follow-imports=silent", "--no-incremental", "-c", snippet]
    )
    assert status == 0, stdout + stderr
