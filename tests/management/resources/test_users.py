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
