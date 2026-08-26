import httpx
import respx


@respx.mock
def test_users_lists(client) -> None:
    base = "https://api.modus.com/api/v1/users"
    respx.get(f"{base}/member-groups").mock(return_value=httpx.Response(
        200, json={"groups": [], "nextPageToken": None},
    ))
    respx.get(f"{base}/org-members").mock(return_value=httpx.Response(
        200, json={"members": [], "nextPageToken": None},
    ))
    assert client.users.list_member_groups() == []
    assert client.users.list_org_members() == []


@respx.mock
def test_list_member_groups_native_and_directory_rows(client) -> None:
    """Native groups still carry member_ids; directory groups omit it and carry member_count.

    The directory row below has no `member_ids` key at all. Before `member_ids` became
    optional on `MemberGroupDto`, this exact `model_validate()` call (inside
    `list_member_groups`) raised `pydantic.ValidationError` for any directory-sourced
    row — this test is the regression guard for that break.
    """
    base = "https://api.modus.com/api/v1/users"
    native_row = {
        "uid": "grp_native_1",
        "name": "Everyone",
        "description": "All org members",
        "member_ids": ["user_1", "user_2"],
        "created_at": "2026-01-01T00:00:00.000Z",
        "updated_at": "2026-01-01T00:00:00.000Z",
        "source": "native",
    }
    directory_row = {
        "uid": "grp_directory_1",
        "name": "Engineering",
        "description": "Synced from Okta",
        "created_at": "2026-01-02T00:00:00.000Z",
        "updated_at": "2026-01-02T00:00:00.000Z",
        "source": "directory",
        "member_count": 42,
    }
    respx.get(f"{base}/member-groups").mock(return_value=httpx.Response(
        200, json={"groups": [native_row, directory_row], "nextPageToken": None},
    ))

    groups = client.users.list_member_groups()

    assert len(groups) == 2
    native, directory = groups

    assert native.uid == "grp_native_1"
    assert native.source == "native"
    assert native.member_ids == ["user_1", "user_2"]
    assert native.member_count is None

    assert directory.uid == "grp_directory_1"
    assert directory.source == "directory"
    assert directory.member_ids is None
    assert directory.member_count == 42
