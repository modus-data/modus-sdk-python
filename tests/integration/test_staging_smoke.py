"""
Staging journey smoke — real PAT against staging (or any reachable API).

Env:
  MODUS_API_KEY     required (staging PAT)
  MODUS_BASE_URL    default https://api.staging.getmodus.com when unset in CI
  MODUS_AGENT_HOST  default https://agent.staging.getmodus.com (chat/stream)
  MODUS_SMOKE_MODEL default claude-sonnet-5
  MODUS_SCOPE_ID    optional numeric scope id for get / get_context (a slug is a 400 BadRequestError)

Run:
  export MODUS_API_KEY=modus_...
  export MODUS_BASE_URL=https://api.staging.getmodus.com
  uv run pytest tests/integration/test_staging_smoke.py -m integration -v
"""
from __future__ import annotations

import os
import time
import uuid
import warnings
from datetime import datetime, timedelta, timezone

import pytest
from modus import AuthenticationError, BadRequestError, Modus, NotFoundError
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


# The designated smoke org's mined context is its Slack workspace (STAGING-SMOKE.md).
ORG_WIDE_COMPOSE_QUERY = "sdk staging smoke — which Slack channels does this workspace have"

# The server stores "[SDK Staging Smoke]-files-…" as "_SDK_Staging_Smoke_-files-…".
_UPLOAD_FIXTURE_PREFIX = "_SDK_Staging_Smoke_-"


def _delete_stale_upload_fixtures(mgmt: ModusManagement) -> int:
    """Delete the context files earlier smoke runs uploaded (Python, TypeScript and CLI).

    Left in place they pile up in the org this smoke composes against (~95 had,
    a third of its items). Files under an hour old may belong to a run still in
    flight, so they stay.
    """
    cutoff = datetime.now(timezone.utc) - timedelta(hours=1)
    # Collect first: deleting mid-iteration shifts later pages and skips items.
    stale = [
        item.uid
        for item in mgmt.context.items.list(context_type="file_upload", page_size=200).auto_paging_iter()
        if str((item.content or {}).get("fileName") or "").startswith(_UPLOAD_FIXTURE_PREFIX)
        and datetime.fromisoformat(str(item.created_at).replace("Z", "+00:00")) < cutoff
    ]
    for uid in stale:
        try:
            mgmt.context.items.delete(uid)
        except NotFoundError:
            pass  # another smoke run (the other SDK's publish) deleted it first
    return len(stale)


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
    # Scope compose on the agent host (#9894) serves only a published scope the caller may use;
    # any other id is its 404 "Scope not found", whatever the first listed scope happens to be.
    compose_scope_id = os.getenv("MODUS_SCOPE_ID") or next(
        (str(s.id) for s in scopes.items if s.active_variation_id and s.can_use), None
    )

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
    #
    # `is not None` passed for months while the org-wide endpoint was returning
    # nothing, because an empty composition is still an object. Assert the
    # contract instead, and bound the latency: the incident this smoke missed was
    # a 90s hang that the edge turned into a 503 at 30s, which no assertion about
    # the body can catch.
    def assert_composition(label: str, composed: object, elapsed_s: float) -> None:
        assert composed is not None, f"{label}: no response"
        assert isinstance(composed.context, str), f"{label}: context"
        assert isinstance(composed.original_count, (int, float)), f"{label}: original_count"
        assert isinstance(composed.selected_count, (int, float)), f"{label}: selected_count"
        assert composed.session_id, f"{label}: session_id"

        # Compose runs on the agent host, which has no 30 s edge limit; the
        # server stops a compose at 90 s with a 504, so a 200 is always under it.
        assert elapsed_s < 95, f"{label}: took {elapsed_s:.1f}s; the server deadline is 90s"

    # Every compose must reach the agent host's route, never the API host's
    # deprecated one behind the 30 s gateway limit.
    compose_urls: list[str] = []
    client._http._client.event_hooks["request"].append(
        lambda request: compose_urls.append(str(request.url)) if "/context" in request.url.path else None
    )

    _delete_stale_upload_fixtures(mgmt)
    started = time.monotonic()
    composed = client.modus.get_context(ORG_WIDE_COMPOSE_QUERY, limit=3)
    assert_composition("org-wide get_context", composed, time.monotonic() - started)
    # The composer renders nothing, as a success, when it judges every candidate
    # irrelevant; this query is one the org can answer, so empty context is a failure.
    assert composed.context, (
        f"org-wide get_context: rendered no context (original_count={composed.original_count})"
    )

    if compose_scope_id:
        started = time.monotonic()
        scope_composed = client.scopes.get_context(
            compose_scope_id, "sdk staging smoke — brief context", limit=3
        )
        assert_composition("scope get_context", scope_composed, time.monotonic() - started)
    else:
        warnings.warn("scope get_context SKIPPED: no published scope in the first 5 (set MODUS_SCOPE_ID)", stacklevel=1)

    agent_host = client._config.agent_host
    assert compose_urls, "no compose request recorded"
    assert all(url.startswith(f"{agent_host}/agent/v1/") for url in compose_urls), compose_urls

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

    # Errors — an id past int4 is a 404 from the id pipe (#9760) with the parsed envelope
    # (#9757); a slug is a 400. The full id table is in test_staging_journeys.py.
    with pytest.raises(NotFoundError) as missing:
        client.scopes.get(2_147_483_648)
    assert missing.value.code == "NOT_FOUND"
    assert missing.value.info == {"id": 2_147_483_648}
    assert (missing.value.request_id or "").startswith("req_")
    with pytest.raises(BadRequestError) as slug:
        client.scopes.get("revenue-analysis")
    assert slug.value.code == "BAD_REQUEST"
    assert (slug.value.request_id or "").startswith("req_")

    bad = Modus(
        api_key="modus_00000000_dead_beef_invalid_key_for_smoke",
        base_url=_base_url(),
        timeout=30.0,
    )
    with pytest.raises(AuthenticationError) as unauthenticated:
        bad.scopes.list(page_size=1)
    assert unauthenticated.value.code == "UNAUTHORIZED"
    assert (unauthenticated.value.request_id or "").startswith("req_")


@pytest.mark.skipif(not _has_live, reason="MODUS_API_KEY not set")
def test_staging_context_files_upload(tmp_path) -> None:
    """Presign → PUT → finalize via mgmt.context.files.upload (Moonactive path)."""
    from pathlib import Path

    mgmt = _mgmt()
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    run_id = uuid.uuid4().hex[:8]
    file_path = Path(tmp_path) / f"[SDK Staging Smoke]-files-{stamp}-{run_id}.txt"
    file_path.write_text("sdk staging smoke context file — deleted by the next run\n", encoding="utf-8")

    uploaded = mgmt.context.files.upload(file_path, wait_until="processing")
    assert uploaded.upload_id
    assert uploaded.status in ("processing", "ready")

    got = mgmt.context.files.get(uploaded.upload_id)
    assert got.upload_id == uploaded.upload_id
    assert got.status in ("processing", "ready")


@pytest.mark.skipif(not _has_live, reason="MODUS_API_KEY not set")
def test_staging_chat_and_stream() -> None:
    """chat() result and live stream against the staging agent host (hard gate)."""
    model = os.getenv("MODUS_SMOKE_MODEL") or "claude-sonnet-5"
    agent_host = os.getenv("MODUS_AGENT_HOST") or "https://agent.staging.getmodus.com"
    client = Modus(base_url=_base_url(), agent_host=agent_host, timeout=180.0)

    awaited = client.modus.chat(
        "sdk staging smoke — reply with one short word",
        model=model,
    ).result()
    assert awaited.content
    assert awaited.thread_id

    with client.modus.chat(
        "sdk staging smoke — stream one short word",
        model=model,
        thread_id=awaited.thread_id,
    ) as stream:
        tokens = list(stream.text_stream)
        final = stream.result()

    assert tokens
    assert final.content
    assert final.thread_id or final.run_id

    # create_modus must mint sessionId + negotiate SSE (not JSON pending). A token run
    # synthesizes the org's full environment (#9693), so pin the cheapest admitted model,
    # and ask for nothing a write tool could do: a write would stop at approval_required.
    create_tokens = 0
    for event in client.workflows.runs.create_modus(
        {
            "message": "sdk staging smoke — reply with one short word, use no tools",
            "config": {"model": "gpt-oss-20b"},
        }
    ):
        content = getattr(event, "content", None)
        if getattr(event, "type", None) == "token" and isinstance(content, str) and content:
            create_tokens += 1
    assert create_tokens > 0
