"""
Staging journeys — the release-gate scenarios of the API test plan (J1, J2, J4, J6, J8), live,
for the sync and the async client.

Same env as test_staging_smoke.py. Optional:
  MODUS_READ_API_KEY    a read-only PAT in the same org, for the 403 ``info.missing`` check
  MODUS_EVAL_SCOPE_ID   a scope with completed evaluation runs, for the J8 model-fidelity reads
  MODUS_APPROVAL_SCOPE_ID  a published scope whose one tool is approval-gated and writes nothing, for J2.4
  MODUS_MEMBER_API_KEY  another member's PAT in the same org, for J2.4's 404 on their resume

Every check counts the requests it sends and asserts the whole error envelope
(``{error:{code,status,message,requestId,info}}``), not only the exception class.
Everything it creates is named ``[API-Cleanse]`` and deleted at the end of the module.

Run:
  uv run pytest tests/integration/test_staging_journeys.py -m integration -v
"""
from __future__ import annotations

import inspect
import json
import os
import threading
import time
import uuid
import warnings
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional

import httpx
import pytest
from modus import (
    AsyncModus,
    AuthenticationError,
    BadRequestError,
    ConflictError,
    Modus,
    ModusError,
    NotFoundError,
    PermissionDeniedError,
    ValidationError,
)
from modus._generated.models import UpdateAgentInterfaceDto
from modus.management import (
    AgentSelection,
    AgentTrigger,
    AsyncModusManagement,
    MemoryUpdate,
    ModusManagement,
    Toolset,
)

pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(not os.getenv("MODUS_API_KEY"), reason="MODUS_API_KEY not set"),
]

BASE = (os.getenv("MODUS_BASE_URL") or "https://api.staging.getmodus.com").rstrip("/")
AGENT = (os.getenv("MODUS_AGENT_HOST") or BASE.replace("//api.", "//agent.")).rstrip("/")
# The cheapest model the run policy admits; these journeys check plumbing, not answers.
MODEL = "gpt-oss-20b"
PREFIX = "[API-Cleanse] smoke-py"
STAMP = f"{datetime.now(timezone.utc):%H%M%S}-{uuid.uuid4().hex[:6]}"
MISSING_UUID = "00000000-0000-4000-8000-000000000000"

# Every request the clients below send, so a check can assert how many went out.
SENT: List[str] = []


def _record(request: httpx.Request) -> None:
    SENT.append(f"{request.method} {request.url}")


async def _arecord(request: httpx.Request) -> None:
    _record(request)


def counted(client: Any, is_async: bool = False) -> Any:
    hook = _arecord if is_async else _record
    for http in {id(h): h for h in (client._http, getattr(client, "_agent_http", client._http))}.values():
        hooks = http._client.event_hooks
        http._client.event_hooks = {"request": [*hooks.get("request", []), hook], "response": hooks.get("response", [])}
    return client


def dump(model: Any) -> Dict[str, Any]:
    return model.model_dump(by_alias=True, mode="json")


def check_envelope(e: ModusError, status: int, code: str, grpc: str, info: Any, requests: int) -> None:
    assert (e.status_code, e.code) == (status, code)
    assert e.request_id and e.request_id.startswith("req_")
    envelope = json.loads(e.body or "{}")["error"]
    assert envelope["code"] == code and envelope["status"] == grpc
    assert envelope["requestId"] == e.request_id
    assert envelope["message"] and envelope["message"] == e.message
    if status >= 500 or info == "absent":
        assert "info" not in envelope
    elif info is not None:
        assert envelope["info"] == info and e.info == info
    assert len(SENT) == requests, SENT


def expect_api_error(call: Callable[[], Any], cls: type, status: int, code: str, grpc: str,
                     info: Any = None, requests: int = 1) -> ModusError:
    """``call`` fails with the whole expected envelope after exactly ``requests`` requests."""
    SENT.clear()
    with pytest.raises(cls) as caught:
        call()
    check_envelope(caught.value, status, code, grpc, info, requests)
    return caught.value


async def aexpect_api_error(call: Callable[[], Any], cls: type, status: int, code: str, grpc: str,
                            info: Any = None, requests: int = 1) -> ModusError:
    SENT.clear()
    with pytest.raises(cls) as caught:
        await call()
    check_envelope(caught.value, status, code, grpc, info, requests)
    return caught.value


def expect_local_refusal(call: Callable[[], Any]) -> None:
    SENT.clear()
    with pytest.raises(ValidationError):
        call()
    assert SENT == []


async def aexpect_local_refusal(call: Callable[[], Any]) -> None:
    SENT.clear()
    with pytest.raises(ValidationError):
        await call()
    assert SENT == []


NOT_FOUND = dict(cls=NotFoundError, status=404, code="NOT_FOUND", grpc="NOT_FOUND")
BAD_REQUEST = dict(cls=BadRequestError, status=400, code="BAD_REQUEST", grpc="INVALID_ARGUMENT")
ID_NOT_FOUND = [
    (2147483647, {"scopeId": 2147483647}),
    (2147483648, {"id": 2147483648}),
    (0, {"id": 0}),
    (-1, {"id": -1}),
]
ID_BAD_REQUEST = ["1.5", "revenue-analysis"]
ID_LOCAL = ["", ".", ".."]


def drain(events: Any) -> Dict[str, Any]:
    text, types = "", []
    for e in events:
        types.append(e.type)
        if e.type == "token":
            text += e.content or ""
    return {"text": text, "types": types}


async def adrain(events: Any) -> Dict[str, Any]:
    text, types = "", []
    async for e in events:
        types.append(e.type)
        if e.type == "token":
            text += e.content or ""
    return {"text": text, "types": types}


@pytest.fixture(scope="module")
def client() -> Modus:
    return counted(Modus(base_url=BASE, timeout=180.0))


@pytest.fixture(scope="module")
def mgmt() -> ModusManagement:
    return counted(ModusManagement(base_url=BASE, timeout=120.0))


@pytest.fixture(scope="module")
def scopes(mgmt: ModusManagement):
    """A draft main scope and a manager scope, deleted at the end of the module."""
    main = int(mgmt.scopes.create(
        f"{PREFIX} main {STAMP}",
        description="smoke description",
        expected_output="smoke expected output",
        instructions=["smoke instruction"],
    ).id)
    manager = int(mgmt.scopes.create(f"{PREFIX} manager {STAMP}").id)
    made = {"main": main, "manager": manager, "deleted": set(), "workflow": None}
    yield made
    if made["workflow"] is not None:
        try:
            mgmt.workflows.delete(made["workflow"])
        except ModusError:
            pass
    for sid in (main, manager):
        if sid not in made["deleted"]:
            try:
                mgmt.scopes.delete(sid)
            except ModusError:
                pass


# --------------------------------------------------------------------------- J4 / J3 sync


@pytest.mark.parametrize("scope_id,info", ID_NOT_FOUND)
def test_id_not_found(client: Modus, scope_id: int, info: dict) -> None:
    expect_api_error(lambda: client.scopes.get(scope_id), **NOT_FOUND, info=info)


@pytest.mark.parametrize("scope_id", ID_BAD_REQUEST)
def test_id_bad_request(client: Modus, scope_id: str) -> None:
    expect_api_error(lambda: client.scopes.get(scope_id), **BAD_REQUEST)


@pytest.mark.parametrize("scope_id", ID_LOCAL)
def test_id_refused_locally(client: Modus, scope_id: str) -> None:
    expect_local_refusal(lambda: client.scopes.get(scope_id))


def test_float_id_is_the_same_scope(client: Modus, scopes: dict) -> None:
    SENT.clear()
    assert int(client.scopes.get(float(scopes["main"])).id) == scopes["main"]
    assert len(SENT) == 1


def test_page_size_edges(client: Modus) -> None:
    expect_local_refusal(lambda: client.scopes.list(page_size=0))
    expect_api_error(lambda: client.scopes.list(page_size=101), **BAD_REQUEST)


def test_bad_key_envelope() -> None:
    bad = counted(Modus(api_key="modus_00000000_dead_beef_invalid_key_for_smoke", base_url=BASE))
    expect_api_error(lambda: bad.scopes.list(page_size=1), cls=AuthenticationError, status=401,
                     code="UNAUTHORIZED", grpc="UNAUTHENTICATED", info="absent")


@pytest.mark.skipif(not os.getenv("MODUS_READ_API_KEY"), reason="MODUS_READ_API_KEY not set")
def test_read_only_key_403_names_the_missing_scope() -> None:
    read_only = counted(ModusManagement(api_key=os.environ["MODUS_READ_API_KEY"], base_url=BASE))
    expect_api_error(lambda: read_only.scopes.create(f"{PREFIX} never-created {STAMP}"),
                     cls=PermissionDeniedError, status=403, code="FORBIDDEN", grpc="PERMISSION_DENIED",
                     info={"required": ["scopes:write"], "missing": ["scopes:write"]})
    # Positive control: the same key reads, so the 403 is about the scope, not a dead key.
    assert isinstance(Modus(api_key=os.environ["MODUS_READ_API_KEY"], base_url=BASE).scopes.list(page_size=1).items, list)


# #9894: org-wide compose takes 26-84 s on staging, past API Gateway's 30 s cut on modus-api, so it
# runs on the agent host (90 s deadline). The latency bound stays in test_staging_smoke.py.
def test_org_wide_compose_is_served_by_the_agent_host(client: Modus) -> None:
    SENT.clear()
    composed = client.modus.get_context("sdk staging smoke — list relevant tables", limit=3)
    assert [httpx.URL(r.split(" ")[1]).host for r in SENT] == [httpx.URL(AGENT).host]
    assert isinstance(composed.context, str) and composed.session_id


# --------------------------------------------------------------------------- J6 sync


def test_nested_update_mask_leaves_access_config(mgmt: ModusManagement, scopes: dict) -> None:
    before = mgmt.scopes.get(scopes["main"], view="draft")
    SENT.clear()
    after = mgmt.scopes.update(scopes["main"], name=f"{PREFIX} main2 {STAMP}",
                               update_mask="name,accessConfig.visibility")
    assert len(SENT) == 1
    assert after.name == f"{PREFIX} main2 {STAMP}"
    assert dump(after)["accessConfig"] == dump(before)["accessConfig"]


def test_masked_field_left_unset_is_cleared(mgmt: ModusManagement, scopes: dict) -> None:
    SENT.clear()
    mgmt.scopes.update(scopes["main"], name=f"{PREFIX} main3 {STAMP}", update_mask="name,expectedOutput")
    assert len(SENT) == 1, "PATCH re-sent: the server failed"
    variation = dump(mgmt.scopes.get(scopes["main"], view="draft"))["variation"]
    assert not variation.get("expectedOutput")
    assert variation.get("instructions") == ["smoke instruction"]


def test_omitted_field_kept_and_non_clearable_name_is_400(mgmt: ModusManagement, scopes: dict) -> None:
    mgmt.scopes.update(scopes["main"], description="kept description")
    mgmt.scopes.update(scopes["main"], name=f"{PREFIX} main4 {STAMP}")
    assert dump(mgmt.scopes.get(scopes["main"], view="draft"))["description"] == "kept description"
    expect_api_error(lambda: mgmt.scopes.update(scopes["main"], update_mask="name"), **BAD_REQUEST)
    assert mgmt.scopes.get(scopes["main"], view="draft").name == f"{PREFIX} main4 {STAMP}"


def test_manager_id_int_filter_and_detach(client: Modus, mgmt: ModusManagement, scopes: dict) -> None:
    mgmt.scopes.update(scopes["main"], manager_id=scopes["manager"])
    manager = dump(mgmt.scopes.get(scopes["manager"], view="draft"))["variation"]
    assert str(scopes["main"]) in [str(s) for s in manager.get("supervisionSubordinateIds") or []]
    listed = client.scopes.list(manager_id=scopes["manager"], page_size=100)
    assert [int(s.id) for s in listed.items] == [scopes["main"]]
    mgmt.scopes.update(scopes["main"], update_mask="managerId")


def test_toolset_empty_clears_tools(mgmt: ModusManagement, scopes: dict) -> None:
    mgmt.scopes.update(scopes["main"], toolset=Toolset.memory())
    mgmt.scopes.update(scopes["main"], toolset=Toolset.empty())
    toolset = dump(mgmt.scopes.get(scopes["main"], view="draft"))["variation"]["toolset"]
    assert toolset == {}


def test_missing_memory_is_404(mgmt: ModusManagement, scopes: dict) -> None:
    memories = mgmt.scopes.memories(scopes["main"])
    expect_api_error(lambda: memories.update(MISSING_UUID, MemoryUpdate(memory="x")), **NOT_FOUND)
    expect_api_error(lambda: memories.delete(MISSING_UUID), **NOT_FOUND)


def test_dotdot_memory_delete_sends_nothing(client: Modus, mgmt: ModusManagement, scopes: dict) -> None:
    expect_local_refusal(lambda: mgmt.scopes.memories(scopes["main"]).delete(".."))
    assert int(client.scopes.get(scopes["main"]).id) == scopes["main"]


def test_draft_run_is_403_before_any_token(client: Modus, scopes: dict) -> None:
    expect_api_error(
        lambda: drain(client.workflows.runs.create_scope(
            scopes["main"], {"message": "hi", "version": "draft", "config": {"model": MODEL}})),
        cls=PermissionDeniedError, status=403, code="FORBIDDEN", grpc="PERMISSION_DENIED")


def test_deployed_scope_chat_streams_and_lists_conversation(client: Modus, mgmt: ModusManagement,
                                                            scopes: dict) -> None:
    mgmt.scopes.deploy(scopes["main"])
    started = time.monotonic()
    first_token: Optional[float] = None
    with client.scopes.chat(scopes["main"], "Reply with exactly one short word.", model=MODEL) as s:
        tokens = []
        for t in s.text_stream:
            if t:
                first_token = first_token if first_token is not None else time.monotonic() - started
                tokens.append(t)
        final = s.result()
    assert tokens and final.content
    assert first_token is not None and first_token < 10, f"time to first token {first_token}s"
    threads = [t.thread_id for t in client.scopes.conversations(scopes["main"]).list(page_size=10).items]
    assert final.thread_id in threads


def test_workflow_without_guardrails_interface_400_deploy_disable(mgmt: ModusManagement, scopes: dict) -> None:
    assert "guardrails" not in inspect.signature(mgmt.workflows.create).parameters
    assert "guardrails" not in inspect.signature(mgmt.workflows.update).parameters
    wf = mgmt.workflows.create(f"{PREFIX} workflow {STAMP}", "workflow", trigger=AgentTrigger.manual(),
                               agent_selection=AgentSelection.single(scopes["main"]))
    wf_id = scopes["workflow"] = int(wf.id)
    expect_api_error(lambda: mgmt.workflows.interfaces(wf_id).update("not-a-uuid", UpdateAgentInterfaceDto(name="x")),
                     **BAD_REQUEST)
    # Positive control: the same workflow's interfaces are reachable.
    assert isinstance(mgmt.workflows.interfaces(wf_id).list(), list)
    mgmt.workflows.deploy(wf_id)
    assert mgmt.workflows.toggle(wf_id, active=False).is_enabled is False
    assert mgmt.workflows.get(wf_id).is_enabled is False


def test_workflow_description_clears_and_name_is_not_clearable(mgmt: ModusManagement, scopes: dict) -> None:
    wf_id = scopes["workflow"]
    assert wf_id is not None
    mgmt.workflows.update(wf_id, description="wf description")
    mgmt.workflows.update(wf_id, update_mask="description")
    assert not dump(mgmt.workflows.get(wf_id, view="draft")).get("description")
    expect_api_error(lambda: mgmt.workflows.update(wf_id, update_mask="name"), **BAD_REQUEST)
    assert mgmt.workflows.get(wf_id).name == f"{PREFIX} workflow {STAMP}"


def test_second_scope_delete_is_404(mgmt: ModusManagement, scopes: dict) -> None:
    mgmt.scopes.delete(scopes["manager"])
    scopes["deleted"].add(scopes["manager"])
    expect_api_error(lambda: mgmt.scopes.delete(scopes["manager"]), **NOT_FOUND)


# --------------------------------------------------------------------------- J1 sync


def test_derived_agent_host_streams_and_second_turn_keeps_context(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("MODUS_AGENT_HOST", raising=False)
    derived = counted(Modus(base_url=BASE, timeout=180.0))
    SENT.clear()
    started = time.monotonic()
    first_token: Optional[float] = None
    with derived.modus.chat("My favourite fruit is the tangerine. Reply with exactly: noted", model=MODEL) as s:
        for token in s.text_stream:
            if token and first_token is None:
                first_token = time.monotonic() - started
        final = s.result()
    assert len(SENT) == 1 and httpx.URL(SENT[0].split(" ")[1]).host == httpx.URL(BASE).host.replace("api.", "agent.", 1)
    assert final.content and final.thread_id
    reply = derived.modus.chat("What is my favourite fruit? Reply with one word.", model=MODEL,
                               thread_id=final.thread_id).result()
    assert "tangerine" in reply.content.lower()
    convo = derived.modus.conversations.get(final.thread_id)
    assert [m["type"] for m in dump(convo)["messages"]].count("human") == 2
    # Not gated: org-wide composition runs before the first token and takes 17-34 s on staging
    # (composer latency, finding F2, owner nirch). The 10 s bound is gated on the scope chat above.
    print(f"org chat time to first token: {first_token}s")


def test_custom_base_url_without_agent_host_is_a_config_error(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("MODUS_AGENT_HOST", raising=False)

    def blocked(request: httpx.Request) -> httpx.Response:
        SENT.append(f"{request.method} {request.url}")
        raise httpx.ConnectError("blocked by the smoke", request=request)

    custom = Modus(api_key="modus_00000000_fake", base_url="https://modus.example.internal", max_retries=0)
    for http in {id(h): h for h in (custom._http, custom._agent_http)}.values():
        http._client._transport = httpx.MockTransport(blocked)
    SENT.clear()
    with pytest.raises(ModusError, match="(?i)agent host"):
        custom.modus.chat("x", model=MODEL).result()
    assert SENT == []


def test_chat_content_names_the_new_spelling_without_sending() -> None:
    """#9704: chat() returns a session; the old `.content` spelling says what to write instead."""
    SENT.clear()
    chat = counted(Modus(base_url=BASE)).modus.chat("x", model=MODEL)
    with pytest.raises(AttributeError, match=r"chat\.result\(\)\.content"):
        chat.content  # noqa: B018
    achat = counted(AsyncModus(base_url=BASE), is_async=True).modus.chat("x", model=MODEL)
    with pytest.raises(AttributeError, match=r"\(await chat\)\.content"):
        achat.content  # noqa: B018
    assert SENT == []


def test_high_level_chat_refuses_unknown_model_locally(client: Modus) -> None:
    def call() -> None:
        client.modus.chat("hi", model="not-a-model").result()
    expect_local_refusal(call)


def test_closing_the_stream_does_not_cancel_the_run(client: Modus) -> None:
    runs, run_id = client.workflows.runs, str(uuid.uuid4())
    events = runs.create_modus({"message": "Count from 1 to 60, one number per line, no other text.",
                                "runId": run_id, "config": {"model": MODEL}})
    for e in events:
        if e.type == "token" and e.content:
            break
    events.close()
    rest = drain(runs.stream(run_id))
    assert rest["types"][-1] == "done" and "60" in rest["text"]


# #9867: before it events dropped the SSE id and runs.stream took no last_event_id.
def test_run_stream_resumes_from_an_event_id(client: Modus) -> None:
    runs, run_id = client.workflows.runs, str(uuid.uuid4())
    events = runs.create_modus({"message": "Reply with exactly: ok", "runId": run_id, "config": {"model": MODEL}})
    ids = [e.id for e in events if getattr(e, "id", None)]
    assert ids, "no event carried an SSE id"
    assert drain(runs.stream(run_id, last_event_id=ids[0]))["types"][-1] == "done"


# #9867: before it the resume answered 200 and an SSE error frame, and poisoned the thread.
def test_stale_resume_is_a_409_and_the_conversation_stays_usable(client: Modus) -> None:
    runs = client.workflows.runs
    session_id, run_id = str(uuid.uuid4()), str(uuid.uuid4())
    drain(runs.create_modus({"message": "Reply with exactly: one", "sessionId": session_id, "runId": run_id,
                             "config": {"model": MODEL}}))
    expect_api_error(lambda: drain(runs.resume(run_id, {"sessionId": session_id, "decision": "approve"})),
                     cls=ConflictError, status=409, code="CONFLICT", grpc="ALREADY_EXISTS")
    nxt = drain(runs.create_modus({"message": "Reply with exactly: two", "sessionId": session_id,
                                   "config": {"model": MODEL}}))
    assert "error" not in nxt["types"] and "two" in nxt["text"].lower()


@pytest.mark.parametrize("body,message", [
    ({"message": "hi", "config": {"model": "not-a-model"}}, "Unknown model"),
    ({"message": "x" * 32_001, "config": {"model": MODEL}}, "32000"),
])
def test_raw_run_post_refusal_before_any_event(client: Modus, body: dict, message: str) -> None:
    e = expect_api_error(lambda: drain(client.workflows.runs.create_modus(body)), **BAD_REQUEST, info="absent")
    assert message in e.message


# --------------------------------------------------------------------------- J2 sync


def test_interrupt_running_run(client: Modus) -> None:
    runs = client.workflows.runs
    session_id, run_id = str(uuid.uuid4()), str(uuid.uuid4())
    events = runs.create_modus({"message": "Count from 1 to 400, one number per line, no other text.",
                                "sessionId": session_id, "runId": run_id, "config": {"model": MODEL}})
    admission, types = None, []
    for e in events:
        types.append(e.type)
        if e.type == "token" and admission is None:
            SENT.clear()
            admission = runs.interrupt(run_id, {"message": "Reply with exactly: ok", "sessionId": session_id})
            assert len(SENT) == 1
    assert admission is not None and admission.run_id != run_id and admission.status
    assert types[-1] == "cancelled"
    assert "ok" in drain(runs.stream(admission.run_id))["text"].lower()


def test_edit_queued_turn(client: Modus) -> None:
    runs = client.workflows.runs
    session_id, queued_id = str(uuid.uuid4()), str(uuid.uuid4())
    busy = runs.create_modus({"message": "Count from 1 to 1000, one number per line, no other text.",
                              "sessionId": session_id, "config": {"model": MODEL}})
    next(busy)
    queued = runs.create_modus({"message": "Reply with exactly: original", "sessionId": session_id,
                                "runId": queued_id, "config": {"model": MODEL}})
    # A generator sends nothing until iterated: start the queued POST on a thread.
    worker = threading.Thread(target=lambda: drain(queued), daemon=True)
    worker.start()
    admission = None
    for _ in range(30):
        time.sleep(0.2)
        try:
            admission = runs.edit_queued(queued_id, {"message": "Reply with exactly: edited", "sessionId": session_id})
            break
        except NotFoundError:
            continue
    assert admission is not None and (admission.run_id, admission.status) == (queued_id, "queued")
    busy.close()
    worker.join(120)
    assert "edited" in drain(runs.stream(queued_id))["text"].lower()
    expect_api_error(lambda: runs.edit_queued(queued_id, {"message": "too late", "sessionId": session_id}),
                     cls=ConflictError, status=409, code="CONFLICT", grpc="ALREADY_EXISTS")


def test_interrupt_finished_run_starts_follow_up(client: Modus) -> None:
    runs = client.workflows.runs
    session_id, run_id = str(uuid.uuid4()), str(uuid.uuid4())
    drain(runs.create_modus({"message": "Reply with exactly: one", "sessionId": session_id, "runId": run_id,
                             "config": {"model": MODEL}}))
    admission = runs.interrupt(run_id, {"message": "Reply with exactly: two", "sessionId": session_id})
    assert "two" in drain(runs.stream(admission.run_id))["text"].lower()


def test_blank_session_id_refused_locally(client: Modus) -> None:
    runs, run_id = client.workflows.runs, str(uuid.uuid4())
    expect_local_refusal(lambda: drain(runs.resume(run_id, {"decision": "approve"})))
    expect_local_refusal(lambda: runs.interrupt(run_id, {"message": "x", "sessionId": " "}))
    expect_local_refusal(lambda: runs.edit_queued(run_id, {"message": "x", "sessionId": ""}))


# --------------------------------------------------------------------------- J8 (read-only)


def _check_eval_page_walk(pages: List[Any]) -> None:
    runs = [r for p in pages for r in p.items]
    assert runs, "MODUS_EVAL_SCOPE_ID has no evaluation runs"
    assert len({r.id for r in runs}) == len(runs), "duplicate run across pages"
    for r in runs:
        assert isinstance(r.started_at, datetime) and r.started_at.tzinfo is not None
        assert r.finished_at is None or r.finished_at.tzinfo is not None
        assert r.avg_score is None or isinstance(r.avg_score, (int, float))
    keys = [(r.started_at, r.id) for r in runs]
    assert keys == sorted(keys, reverse=True), "not started_at DESC, id DESC"
    # Known residue G2-5: skill_id parses as a float. The G2-5 fix flips this assertion.
    assert isinstance(runs[0].skill_id, float)


@pytest.mark.skipif(not os.getenv("MODUS_EVAL_SCOPE_ID"), reason="MODUS_EVAL_SCOPE_ID not set")
def test_eval_runs_parse_sync(mgmt: ModusManagement) -> None:
    evals = mgmt.scopes.evaluations(int(os.environ["MODUS_EVAL_SCOPE_ID"]))
    pages = [evals.list_runs(page_size=1)]
    while pages[-1].next_page_token and len(pages) < 3:
        pages.append(evals.list_runs(page_size=1, page_token=pages[-1].next_page_token))
    _check_eval_page_walk(pages)
    detail = evals.get_run(pages[0].items[0].id)
    assert detail.id == pages[0].items[0].id and detail.started_at.tzinfo is not None
    for result in detail.results:
        assert result.score is None or isinstance(result.score, (int, float))


@pytest.mark.skipif(not os.getenv("MODUS_EVAL_SCOPE_ID"), reason="MODUS_EVAL_SCOPE_ID not set")
async def test_eval_runs_parse_async() -> None:
    evals = AsyncModusManagement(base_url=BASE).scopes.evaluations(int(os.environ["MODUS_EVAL_SCOPE_ID"]))
    pages = [await evals.list_runs(page_size=1)]
    while pages[-1].next_page_token and len(pages) < 3:
        pages.append(await evals.list_runs(page_size=1, page_token=pages[-1].next_page_token))
    _check_eval_page_walk(pages)
    detail = await evals.get_run(pages[0].items[0].id)
    assert detail.id == pages[0].items[0].id and detail.started_at.tzinfo is not None


# --------------------------------------------------------------------------- async client: same tables


async def test_async_ids_page_sizes_and_bad_key() -> None:
    client = counted(AsyncModus(base_url=BASE, timeout=60.0), is_async=True)
    for scope_id, info in ID_NOT_FOUND:
        await aexpect_api_error(lambda: client.scopes.get(scope_id), **NOT_FOUND, info=info)
    for scope_id in ID_BAD_REQUEST:
        await aexpect_api_error(lambda: client.scopes.get(scope_id), **BAD_REQUEST)
    for scope_id in ID_LOCAL:
        await aexpect_local_refusal(lambda: client.scopes.get(scope_id))
    await aexpect_local_refusal(lambda: client.scopes.list(page_size=0))
    await aexpect_api_error(lambda: client.scopes.list(page_size=101), **BAD_REQUEST)
    bad = counted(AsyncModus(api_key="modus_00000000_dead_beef_invalid_key_for_smoke", base_url=BASE), is_async=True)
    await aexpect_api_error(lambda: bad.scopes.list(page_size=1), cls=AuthenticationError, status=401,
                            code="UNAUTHORIZED", grpc="UNAUTHENTICATED", info="absent")


def amgmt() -> AsyncModusManagement:
    return counted(AsyncModusManagement(base_url=BASE, timeout=120.0), is_async=True)


async def test_async_masked_field_left_unset_is_cleared(scopes: dict) -> None:
    mgmt, main = amgmt(), scopes["main"]
    SENT.clear()
    await mgmt.scopes.update(main, name=f"{PREFIX} main-async {STAMP}", update_mask="name,description")
    assert len(SENT) == 1, "PATCH re-sent: the server failed"
    assert not dump(await mgmt.scopes.get(main, view="draft")).get("description")


async def test_async_missing_memory_is_404_and_dotdot_sends_nothing(scopes: dict) -> None:
    memories = amgmt().scopes.memories(scopes["main"])
    await aexpect_local_refusal(lambda: memories.delete(".."))
    await aexpect_api_error(lambda: memories.update(MISSING_UUID, MemoryUpdate(memory="x")), **NOT_FOUND)


async def test_async_chat_refusal_and_follow_up() -> None:
    client = counted(AsyncModus(base_url=BASE, timeout=180.0), is_async=True)
    runs = client.workflows.runs
    e = await aexpect_api_error(
        lambda: adrain(runs.create_modus({"message": "hi", "config": {"model": "not-a-model"}})),
        **BAD_REQUEST, info="absent")
    assert "Unknown model" in e.message
    session_id, run_id = str(uuid.uuid4()), str(uuid.uuid4())
    async with client.modus.chat("Reply with exactly: one", model=MODEL) as s:
        tokens = [t async for t in s.text_stream if t]
        final = await s
    assert tokens and final.content and final.thread_id
    first = await adrain(runs.create_modus({"message": "Reply with exactly: one", "sessionId": session_id,
                                            "runId": run_id, "config": {"model": MODEL}}))
    assert "done" in first["types"]
    admission = await runs.interrupt(run_id, {"message": "Reply with exactly: two", "sessionId": session_id})
    assert "two" in (await adrain(runs.stream(admission.run_id)))["text"].lower()


async def test_async_high_level_chat_refuses_unknown_model_locally() -> None:
    client = counted(AsyncModus(base_url=BASE), is_async=True)

    async def call() -> None:
        await client.modus.chat("hi", model="not-a-model")
    await aexpect_local_refusal(call)


async def test_async_blank_session_id_refused_locally() -> None:
    runs = counted(AsyncModus(base_url=BASE), is_async=True).workflows.runs
    await aexpect_local_refusal(lambda: runs.interrupt(str(uuid.uuid4()), {"message": "x", "sessionId": ""}))


# --------------------------------------------------------------------------- J2.4 write approval on a scope

# The fixture: a published scope whose only tool is approval-gated and cannot write. On staging,
# scope 1553 `[API-Cleanse] approval-fixture`: GitLab "Comment on Issue" pinned by its instructions
# to project_id 0. GitLab ids start at 1, so even an approved call is a 404 there.
APPROVAL_SCOPE = os.getenv("MODUS_APPROVAL_SCOPE_ID")
APPROVAL_SCOPE_ID = int(APPROVAL_SCOPE) if APPROVAL_SCOPE else 0
# The fixture's pinned tool call needs a model that follows it; the cheap one may not call tools.
APPROVAL_MODEL = "claude-sonnet-5"
needs_approval_scope = pytest.mark.skipif(
    not APPROVAL_SCOPE, reason="MODUS_APPROVAL_SCOPE_ID (Actions var SDK_STAGING_APPROVAL_SCOPE_ID) not set")
if os.getenv("MODUS_API_KEY") and not APPROVAL_SCOPE:
    warnings.warn("J2.4 write approval SKIPPED: MODUS_APPROVAL_SCOPE_ID is unset", stacklevel=1)


def check_stopped_for_approval(first: Any) -> None:
    """The turn stopped before the write, on the fixture's call: only then may it be approved."""
    assert first.approval is not None, "the run did not stop for approval"
    assert first.approval.tool_name and first.approval.id
    assert str((first.approval.args or {}).get("project_id")) == "0", first.approval.args


@needs_approval_scope
def test_scope_approval_deny_ends_cleanly_and_the_thread_answers(client: Modus) -> None:
    chat = client.scopes.chat(APPROVAL_SCOPE_ID, "Post the test comment.", model=APPROVAL_MODEL)
    first = chat.result()
    check_stopped_for_approval(first)
    member_key = os.getenv("MODUS_MEMBER_API_KEY")
    # Another member's token cannot answer the owner's approval (404).
    if member_key:
        member = counted(Modus(api_key=member_key, base_url=BASE, timeout=60.0))
        expect_api_error(lambda: drain(member.workflows.runs.resume(
            first.run_id, {"sessionId": first.thread_id, "decision": "deny"})), **NOT_FOUND)
    denied = chat.resume(decision="deny").result()
    assert denied.approval is None and denied.content
    expect_api_error(lambda: chat.resume(decision="deny").result(),
                     cls=ConflictError, status=409, code="CONFLICT", grpc="ALREADY_EXISTS")
    nxt = client.scopes.chat(APPROVAL_SCOPE_ID, "Reply with exactly: pong", model=MODEL,
                             thread_id=first.thread_id).result()
    assert "pong" in nxt.content.lower()


@needs_approval_scope
async def test_async_scope_approval_approve_completes_and_a_second_resume_is_409() -> None:
    client = counted(AsyncModus(base_url=BASE, timeout=180.0), is_async=True)
    chat = client.scopes.chat(APPROVAL_SCOPE_ID, "Post the test comment.", model=APPROVAL_MODEL)
    first = await chat
    check_stopped_for_approval(first)
    done = await chat.resume(decision="approve")
    assert done.approval is None and done.content
    await aexpect_api_error(lambda: chat.resume(decision="approve"),
                            cls=ConflictError, status=409, code="CONFLICT", grpc="ALREADY_EXISTS")


# --------------------------------------------------------------------------- raw contract (client-independent)


@pytest.mark.parametrize("verb", ["interrupt", "queue-edit"])
def test_raw_empty_body_on_run_control_is_400(verb: str) -> None:
    res = httpx.post(f"{AGENT}/agent/v1/runs/{uuid.uuid4()}/{verb}", json={},
                     headers={"Authorization": f"Bearer {os.environ['MODUS_API_KEY']}"}, timeout=30)
    assert res.status_code == 400
    assert res.json()["error"]["code"] == "BAD_REQUEST"
