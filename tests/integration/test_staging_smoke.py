"""
Staging journey smoke — real PAT against staging (or any reachable API).

Env:
  MODUS_API_KEY     required (staging PAT)
  MODUS_BASE_URL    default https://api.staging.getmodus.com when unset in CI
  MODUS_AGENT_HOST  default https://agent.staging.getmodus.com (chat/stream)
  MODUS_SMOKE_MODEL default claude-sonnet-5
  MODUS_SCOPE_ID    optional stable scope id/slug for get / get_context

Run:
  export MODUS_API_KEY=modus_...
  export MODUS_BASE_URL=https://api.staging.getmodus.com
  uv run pytest tests/integration/test_staging_smoke.py -m integration -v
"""
from __future__ import annotations

import os
import uuid
from datetime import datetime, timedelta, timezone

import pytest
from modus import AuthenticationError, Modus, NotFoundError
from modus.management import ModusManagement

pytestmark = pytest.mark.integration

_DEFAULT_STAGING = "https://api.staging.getmodus.com"
_has_live = bool(os.getenv("MODUS_API_KEY"))


def _base_url() -> str:
    return os.getenv("MODUS_BASE_URL") or _DEFAULT_STAGING


def _client() -> Modus:
    return Modus(base_url=_base_url(), timeout=120.0)


def _mgmt() -> ModusManagement:
    return ModusManagement(base_url=_base_url(), timeout=120.0)


@pytest.mark.skipif(not _has_live, reason="MODUS_API_KEY not set")
def test_staging_journey() -> None:
    """Auth → browse → pagination → compose → mgmt reads → note write → errors."""
    client = _client()
    mgmt = _mgmt()
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    run_id = uuid.uuid4().hex[:8]

    # Auth + identity
    scopes = client.scopes.list(page_size=5)
    assert isinstance(scopes.items, list)

    scope_id = os.getenv("MODUS_SCOPE_ID")
    if not scope_id and scopes.items:
        scope_id = str(scopes.items[0].id)

    # Browse (read client)
    if scope_id:
        got = client.scopes.get(scope_id)
        assert got.id is not None
        convos = client.scopes.conversations(scope_id).list(page_size=5)
        assert isinstance(convos.items, list)

    workflows = client.workflows.list(page_size=5)
    assert isinstance(workflows.items, list)
    if workflows.items:
        wf = client.workflows.get(workflows.items[0].id)
        assert wf.id is not None

    notes = client.context.items.list(context_type="note", page_size=1)
    assert isinstance(notes.items, list)

    connections = client.connections.list(page_size=5)
    assert isinstance(connections.items, list)

    suggestions = client.suggestions.list(page_size=5)
    assert isinstance(suggestions.items, list)

    active_runs = client.workflows.runs.active(page_size=5)
    assert isinstance(active_runs.items, list)

    # Pagination (follow token only when present)
    page1 = client.scopes.list(page_size=1)
    if page1.next_page_token:
        page2 = client.scopes.list(page_size=1, page_token=page1.next_page_token)
        assert isinstance(page2.items, list)

    # Compose (org-wide; keep limit tiny)
    composed = client.modus.get_context("sdk staging smoke — list relevant tables", limit=3)
    assert composed is not None

    if scope_id:
        scope_composed = client.scopes.get_context(
            scope_id, "sdk staging smoke — brief context", limit=3
        )
        assert scope_composed is not None

    # Management reads
    mgmt_scopes = mgmt.scopes.list(page_size=5)
    assert isinstance(mgmt_scopes.items, list)
    members = mgmt.users.list_org_members()
    assert isinstance(members, list)

    until = datetime.now(timezone.utc)
    since = until - timedelta(days=1)
    usage = mgmt.usage.list(
        since=since.strftime("%Y-%m-%dT%H:%M:%SZ"),
        until=until.strftime("%Y-%m-%dT%H:%M:%SZ"),
        rollup="day",
    )
    assert usage is not None

    # Write + cleanup (note — ephemeral; always delete)
    title = f"[SDK Staging Smoke] {stamp}-{run_id}"
    uid: str | None = None
    try:
        created = mgmt.context.create_note(title=title, content="staging smoke note — safe to delete")
        uid = created.context_item_id
        item = client.context.items.get(uid)
        updated = mgmt.context.update_note(
            uid,
            title=f"{title} (updated)",
            body="updated by staging smoke",
            existing=item,
        )
        assert updated.uid == uid
    finally:
        if uid is not None:
            mgmt.context.items.delete(uid)

    # Errors — scope path param is numeric (ParseIntPipe); a missing id → 404.
    with pytest.raises(NotFoundError):
        client.scopes.get(999_999_999)

    bad = Modus(
        api_key="modus_00000000_dead_beef_invalid_key_for_smoke",
        base_url=_base_url(),
        timeout=30.0,
    )
    with pytest.raises(AuthenticationError):
        bad.scopes.list(page_size=1)


@pytest.mark.skipif(not _has_live, reason="MODUS_API_KEY not set")
def test_staging_chat_and_stream() -> None:
    """Buffered chat + streaming against staging agent host (hard gate)."""
    model = os.getenv("MODUS_SMOKE_MODEL") or "claude-sonnet-5"
    agent_host = os.getenv("MODUS_AGENT_HOST") or "https://agent.staging.getmodus.com"
    client = Modus(base_url=_base_url(), agent_host=agent_host, timeout=180.0)

    buffered = client.modus.chat(
        "sdk staging smoke — reply with one short word",
        model=model,
    )
    assert buffered.content
    assert buffered.thread_id

    with client.modus.chat_stream(
        "sdk staging smoke — stream one short word",
        model=model,
    ) as stream:
        tokens = list(stream.text_stream)
        final = stream.get_final_result()

    assert tokens
    assert final.content
    assert final.thread_id or final.run_id

    # create_modus must mint sessionId + negotiate SSE (not JSON pending).
    create_tokens = 0
    for event in client.workflows.runs.create_modus(
        {
            "message": "sdk staging smoke — create_modus one short word",
            "config": {"model": model},
        }
    ):
        content = getattr(event, "content", None)
        if getattr(event, "type", None) == "token" and isinstance(content, str) and content:
            create_tokens += 1
    assert create_tokens > 0
