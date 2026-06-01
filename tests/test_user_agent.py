import httpx
import respx
from modus import Modus

BASE = "https://api.modus.com"


@respx.mock
def test_user_agent_header_present_on_get():
    route = respx.get(f"{BASE}/api/v1/skills").mock(
        return_value=httpx.Response(200, json={"skills": [], "nextPageToken": None})
    )
    Modus(api_key="modus_test", base_url=BASE).skills.list()
    ua = route.calls[0].request.headers.get("user-agent", "")
    assert "modus-python/" in ua


@respx.mock
def test_user_agent_contains_python_version():
    route = respx.get(f"{BASE}/api/v1/skills").mock(
        return_value=httpx.Response(200, json={"skills": [], "nextPageToken": None})
    )
    Modus(api_key="modus_test", base_url=BASE).skills.list()
    ua = route.calls[0].request.headers.get("user-agent", "")
    assert "python/" in ua
