"""Tests for mgmt.context.files.* (presigned uploads, upload_from_url, upload/upload_dir helpers)."""

import itertools
import json
import os
import re
import threading
import time

import httpx
import pytest
import respx
from modus._exceptions import ModusError
from modus.management import AsyncModusManagement, ModusManagement
from modus.management.resources.context.files import MAX_BULK_UPLOAD_FILES
from modus.management.types.context_files import (
    FinalizeInput,
    UploadFromUrlInput,
    UploadUrlInput,
)

BASE = "https://api.modus.com"
S3_URL = "https://s3.example.com/tenant-bucket/context_uploads/abc/report.pdf"
SHARED_PUT_URL = "https://s3.example.com/tenant-bucket/context_uploads/shared"
GET_ANY_UPLOAD_ID = re.compile(rf"{re.escape(BASE)}/api/v1/context/files/[^/]+$")
_upload_id_seq = itertools.count(1)


def _client() -> ModusManagement:
    return ModusManagement(api_key="modus_test_key", base_url=BASE)


def _slot_json(upload_id: str = "up-1", *, upload_url: str = S3_URL, file_name: str = "report.pdf") -> dict:
    return {
        "uploadId": upload_id,
        "uploadUrl": upload_url,
        "s3Key": f"context_uploads/{upload_id}/{file_name}",
        "fileName": file_name,
        "contentType": "application/pdf",
        "expiresAt": "2026-08-12T14:15:00.000Z",
    }


def _file_upload_json(upload_id: str = "up-1", status: str = "processing") -> dict:
    return {"uploadId": upload_id, "status": status}


def _upload_urls_side_effect(request: httpx.Request) -> httpx.Response:
    """One slot per requested file, all sharing SHARED_PUT_URL, never a failure."""
    body = json.loads(request.content)
    uploaded = [
        _slot_json(f"batch-up-{next(_upload_id_seq)}", upload_url=SHARED_PUT_URL, file_name=f["fileName"])
        for f in body["files"]
    ]
    return httpx.Response(200, json={"uploaded": uploaded, "failed": []})


def _processing_get_side_effect(request: httpx.Request) -> httpx.Response:
    """GET .../files/{uploadId} → processing, for whichever id was requested."""
    upload_id = request.url.path.rsplit("/", 1)[-1]
    return httpx.Response(200, json=_file_upload_json(upload_id, "processing"))


# --- create_upload_url / create_upload_urls -------------------------------


@respx.mock
def test_create_upload_url():
    route = respx.post(f"{BASE}/api/v1/context/files/uploadUrl").mock(
        return_value=httpx.Response(201, json=_slot_json())
    )
    slot = _client().context.files.create_upload_url(
        file_name="report.pdf", content_type="application/pdf", file_size=1024
    )
    assert slot.upload_id == "up-1"
    assert slot.upload_url == S3_URL
    body = json.loads(route.calls[0].request.read())
    assert body == {"fileName": "report.pdf", "contentType": "application/pdf", "fileSize": 1024}


@respx.mock
def test_create_upload_urls_partial_failure():
    route = respx.post(f"{BASE}/api/v1/context/files/uploadUrls").mock(
        return_value=httpx.Response(
            200,
            json={
                "uploaded": [_slot_json("up-1")],
                "failed": [{"index": 1, "fileName": "malware.exe", "error": "bad type"}],
            },
        )
    )
    result = _client().context.files.create_upload_urls(
        [
            UploadUrlInput(file_name="report.pdf", content_type="application/pdf", file_size=1024),
            UploadUrlInput(file_name="malware.exe", content_type="application/x-msdownload", file_size=10),
        ]
    )
    assert len(result.uploaded) == 1
    assert result.failed[0].file_name == "malware.exe"
    body = json.loads(route.calls[0].request.read())
    assert body["files"][1] == {
        "fileName": "malware.exe",
        "contentType": "application/x-msdownload",
        "fileSize": 10,
    }


def test_create_upload_urls_rejects_empty():
    with pytest.raises(ValueError, match="must not be empty"):
        _client().context.files.create_upload_urls([])


def test_create_upload_urls_rejects_over_max():
    files = [UploadUrlInput(file_name=f"f{i}", content_type="text/plain", file_size=1) for i in range(101)]
    with pytest.raises(ValueError, match="at most 100"):
        _client().context.files.create_upload_urls(files)


# --- upload_from_url / upload_from_urls ------------------------------------


@respx.mock
def test_upload_from_url():
    route = respx.post(f"{BASE}/api/v1/context/files/uploadFromUrl").mock(
        return_value=httpx.Response(201, json=_file_upload_json("up-2", "processing"))
    )
    result = _client().context.files.upload_from_url("https://example.com/r.pdf", file_name="r.pdf")
    assert result.upload_id == "up-2"
    body = json.loads(route.calls[0].request.read())
    assert body == {"url": "https://example.com/r.pdf", "fileName": "r.pdf"}


@respx.mock
def test_upload_from_urls_partial_failure():
    respx.post(f"{BASE}/api/v1/context/files/uploadFromUrls").mock(
        return_value=httpx.Response(
            200,
            json={
                "uploaded": [_file_upload_json("up-3", "processing")],
                "failed": [{"index": 1, "url": "https://blocked.internal/x", "error": "blocked"}],
            },
        )
    )
    result = _client().context.files.upload_from_urls(
        [
            UploadFromUrlInput(url="https://example.com/a.pdf"),
            UploadFromUrlInput(url="https://blocked.internal/x"),
        ]
    )
    assert len(result.uploaded) == 1
    assert result.failed[0].error == "blocked"


def test_upload_from_urls_rejects_empty():
    with pytest.raises(ValueError, match="must not be empty"):
        _client().context.files.upload_from_urls([])


# --- get / list -------------------------------------------------------------


@respx.mock
def test_get():
    respx.get(f"{BASE}/api/v1/context/files/up-4").mock(
        return_value=httpx.Response(200, json=_file_upload_json("up-4", "ready"))
    )
    item = _client().context.files.get("up-4")
    assert item.upload_id == "up-4"
    assert item.status.value == "ready"


@respx.mock
def test_list_pagination():
    route = respx.get(f"{BASE}/api/v1/context/files").mock(
        side_effect=[
            httpx.Response(
                200, json={"files": [_file_upload_json("up-1")], "nextPageToken": "tok-2"}
            ),
            httpx.Response(200, json={"files": [_file_upload_json("up-2")], "nextPageToken": None}),
        ]
    )
    page = _client().context.files.list(page_size=1)
    assert len(page) == 1
    assert route.calls[0].request.url.params["pageSize"] == "1"
    next_page = page.get_next_page()
    assert next_page.items[0].upload_id == "up-2"
    assert not next_page.has_next_page()


# --- upload() ----------------------------------------------------------------


@respx.mock
def test_upload_puts_bytes_and_polls_until_processing(tmp_path):
    file_path = tmp_path / "report.pdf"
    file_path.write_bytes(b"%PDF-1.4 fake content")

    respx.post(f"{BASE}/api/v1/context/files/uploadUrl").mock(
        return_value=httpx.Response(201, json=_slot_json("up-5"))
    )
    put_route = respx.put(S3_URL).mock(return_value=httpx.Response(200))
    # upload() finalizes after the PUT; finalize already returns `processing`,
    # so the default wait_until is satisfied without polling.
    finalize_route = respx.post(f"{BASE}/api/v1/context/files/up-5/finalize").mock(
        return_value=httpx.Response(201, json=_file_upload_json("up-5", "processing"))
    )
    get_route = respx.get(f"{BASE}/api/v1/context/files/up-5").mock(
        return_value=httpx.Response(200, json=_file_upload_json("up-5", "processing"))
    )

    result = _client().context.files.upload(file_path, poll_interval_s=0)

    assert result.status.value == "processing"
    assert finalize_route.called
    assert json.loads(finalize_route.calls[0].request.read())["fileName"] == "report.pdf"
    assert not get_route.called
    assert put_route.calls[0].request.read() == b"%PDF-1.4 fake content"
    assert put_route.calls[0].request.headers["content-type"] == "application/pdf"


@respx.mock
def test_upload_raises_on_put_failure(tmp_path):
    file_path = tmp_path / "report.pdf"
    file_path.write_bytes(b"data")
    respx.post(f"{BASE}/api/v1/context/files/uploadUrl").mock(
        return_value=httpx.Response(201, json=_slot_json("up-6"))
    )
    respx.put(S3_URL).mock(return_value=httpx.Response(403, text="Forbidden"))

    with pytest.raises(ModusError, match="403"):
        _client().context.files.upload(file_path)


def test_upload_rejects_missing_file(tmp_path):
    with pytest.raises(ValueError, match="Not a file"):
        _client().context.files.upload(tmp_path / "nope.pdf")


def test_upload_rejects_bad_wait_until(tmp_path):
    file_path = tmp_path / "a.txt"
    file_path.write_text("hi")
    with pytest.raises(ValueError, match="wait_until"):
        _client().context.files.upload(file_path, wait_until="done")


# --- upload_dir() ------------------------------------------------------------


def _make_tree(tmp_path):
    (tmp_path / "a.txt").write_text("A")
    sub = tmp_path / "sub"
    sub.mkdir()
    (sub / "b.txt").write_text("B")
    hidden_dir = tmp_path / ".hidden"
    hidden_dir.mkdir()
    (hidden_dir / "skip.txt").write_text("skip")
    (tmp_path / ".dotfile").write_text("skip")
    try:
        os.symlink(tmp_path / "a.txt", tmp_path / "link.txt")
    except (OSError, NotImplementedError):
        pass  # symlinks unsupported on this platform — skip check is exercised elsewhere
    return sub


def _stub_finalize():
    """Bulk finalize echoes back whatever it was asked to finalize.

    upload_dir now ends each batch with one finalize call instead of a poll per
    file, so every directory test needs this route.
    """

    def _respond(request):
        body = json.loads(request.read())
        return httpx.Response(
            200,
            json={
                "finalized": [
                    _file_upload_json(u["uploadId"], "processing") for u in body["uploads"]
                ],
                "failed": [],
            },
        )

    return respx.post(f"{BASE}/api/v1/context/files/finalize").mock(side_effect=_respond)


@respx.mock
def test_upload_dir_skips_hidden_and_symlinks_recursive(tmp_path):
    _make_tree(tmp_path)

    url_a = "https://s3.example.com/tenant-bucket/context_uploads/abc/a.txt"
    url_b = "https://s3.example.com/tenant-bucket/context_uploads/abc/b.txt"
    upload_urls_route = respx.post(f"{BASE}/api/v1/context/files/uploadUrls").mock(
        return_value=httpx.Response(
            200,
            json={
                "uploaded": [_slot_json("up-a", upload_url=url_a), _slot_json("up-b", upload_url=url_b)],
                "failed": [],
            },
        )
    )
    respx.put(url_a).mock(return_value=httpx.Response(200))
    respx.put(url_b).mock(return_value=httpx.Response(200))
    respx.get(f"{BASE}/api/v1/context/files/up-a").mock(
        return_value=httpx.Response(200, json=_file_upload_json("up-a", "processing"))
    )
    respx.get(f"{BASE}/api/v1/context/files/up-b").mock(
        return_value=httpx.Response(200, json=_file_upload_json("up-b", "processing"))
    )

    _stub_finalize()
    result = _client().context.files.upload_dir(tmp_path)

    assert len(result.uploaded) == 2
    assert not result.failed
    upload_call = json.loads(upload_urls_route.calls[0].request.read())
    file_names = {f["fileName"] for f in upload_call["files"]}
    assert file_names == {"a.txt", "b.txt"}
    assert not any(name.startswith(".") for name in file_names)


@respx.mock
def test_upload_dir_continue_on_error(tmp_path):
    (tmp_path / "good.txt").write_text("ok")
    (tmp_path / "bad.txt").write_text("bad")

    respx.post(f"{BASE}/api/v1/context/files/uploadUrls").mock(
        return_value=httpx.Response(
            200,
            json={
                "uploaded": [_slot_json("up-good")],
                "failed": [{"index": 0, "fileName": "bad.txt", "error": "not allowed"}],
            },
        )
    )
    respx.put(S3_URL).mock(return_value=httpx.Response(200))
    respx.get(f"{BASE}/api/v1/context/files/up-good").mock(
        return_value=httpx.Response(200, json=_file_upload_json("up-good", "processing"))
    )

    _stub_finalize()
    result = _client().context.files.upload_dir(tmp_path)

    assert len(result.uploaded) == 1
    assert result.uploaded[0].upload_id == "up-good"
    assert len(result.failed) == 1
    assert result.failed[0].error == "not allowed"


@respx.mock
def test_upload_dir_continues_when_stat_fails(tmp_path, monkeypatch):
    from modus.management.resources.context import files as files_mod

    good = tmp_path / "good.txt"
    gone = tmp_path / "gone.txt"
    good.write_text("ok")
    gone.write_text("x")
    # File vanishes between walk and slot sizing (TOCTOU) — must not abort the batch.
    monkeypatch.setattr(files_mod, "_walk_files", lambda root, *, recursive: [good, gone])
    gone.unlink()

    respx.post(f"{BASE}/api/v1/context/files/uploadUrls").mock(
        return_value=httpx.Response(
            200,
            json={"uploaded": [_slot_json("up-good")], "failed": []},
        )
    )
    respx.put(S3_URL).mock(return_value=httpx.Response(200))
    respx.get(f"{BASE}/api/v1/context/files/up-good").mock(
        return_value=httpx.Response(200, json=_file_upload_json("up-good", "processing"))
    )

    _stub_finalize()
    result = _client().context.files.upload_dir(tmp_path)

    assert len(result.uploaded) == 1
    assert len(result.failed) == 1
    assert result.failed[0].path.endswith("gone.txt")


@respx.mock
def test_upload_dir_records_missing_slots_as_failures(tmp_path):
    (tmp_path / "a.txt").write_text("A")
    (tmp_path / "b.txt").write_text("B")

    respx.post(f"{BASE}/api/v1/context/files/uploadUrls").mock(
        return_value=httpx.Response(
            200,
            json={"uploaded": [_slot_json("up-a")], "failed": []},
        )
    )
    respx.put(S3_URL).mock(return_value=httpx.Response(200))
    respx.get(f"{BASE}/api/v1/context/files/up-a").mock(
        return_value=httpx.Response(200, json=_file_upload_json("up-a", "processing"))
    )

    _stub_finalize()
    result = _client().context.files.upload_dir(tmp_path)

    assert len(result.uploaded) == 1
    assert len(result.failed) == 1
    assert "fewer upload slots" in result.failed[0].error


@respx.mock
def test_upload_dir_continue_on_error_when_put_fails(tmp_path):
    (tmp_path / "a.txt").write_text("A")
    (tmp_path / "b.txt").write_text("B")

    url_a = "https://s3.example.com/tenant-bucket/context_uploads/abc/a.txt"
    url_b = "https://s3.example.com/tenant-bucket/context_uploads/abc/b.txt"
    respx.post(f"{BASE}/api/v1/context/files/uploadUrls").mock(
        return_value=httpx.Response(
            200,
            json={
                "uploaded": [
                    _slot_json("up-a", upload_url=url_a),
                    _slot_json("up-b", upload_url=url_b),
                ],
                "failed": [],
            },
        )
    )
    respx.put(url_a).mock(return_value=httpx.Response(200))
    respx.put(url_b).mock(return_value=httpx.Response(500, text="boom"))
    respx.get(f"{BASE}/api/v1/context/files/up-a").mock(
        return_value=httpx.Response(200, json=_file_upload_json("up-a", "processing"))
    )

    _stub_finalize()
    result = _client().context.files.upload_dir(tmp_path)

    assert len(result.uploaded) == 1
    assert len(result.failed) == 1
    assert "500" in result.failed[0].error


def test_upload_dir_rejects_non_directory(tmp_path):
    missing = tmp_path / "nope"
    with pytest.raises(ValueError, match="Not a directory"):
        _client().context.files.upload_dir(missing)


def test_upload_dir_rejects_bad_concurrency(tmp_path):
    with pytest.raises(ValueError, match="concurrency"):
        _client().context.files.upload_dir(tmp_path, concurrency=0)


@respx.mock
def test_upload_dir_pages_create_upload_urls_in_batches_of_100(tmp_path):
    total_files = 130
    for i in range(total_files):
        (tmp_path / f"f{i:03d}.txt").write_text("x")

    upload_urls_route = respx.post(f"{BASE}/api/v1/context/files/uploadUrls").mock(
        side_effect=_upload_urls_side_effect
    )
    respx.put(SHARED_PUT_URL).mock(return_value=httpx.Response(200))
    respx.get(url__regex=GET_ANY_UPLOAD_ID.pattern).mock(side_effect=_processing_get_side_effect)

    _stub_finalize()
    result = _client().context.files.upload_dir(tmp_path, recursive=False)

    assert len(result.uploaded) == total_files
    assert not result.failed
    # 130 files must page into ceil(130 / 100) = 2 create_upload_urls calls, each ≤ 100.
    assert upload_urls_route.call_count == 2
    batch_sizes = [len(json.loads(call.request.content)["files"]) for call in upload_urls_route.calls]
    assert batch_sizes == [100, 30]
    assert all(size <= 100 for size in batch_sizes)


@respx.mock
def test_upload_dir_bounds_concurrency_to_default_10(tmp_path):
    total_files = 14  # > default concurrency, so the bound is actually exercised
    for i in range(total_files):
        (tmp_path / f"f{i:02d}.txt").write_text("x")

    respx.post(f"{BASE}/api/v1/context/files/uploadUrls").mock(side_effect=_upload_urls_side_effect)
    respx.get(url__regex=GET_ANY_UPLOAD_ID.pattern).mock(side_effect=_processing_get_side_effect)

    lock = threading.Lock()
    state = {"in_flight": 0, "max_in_flight": 0}

    def put_side_effect(request: httpx.Request) -> httpx.Response:
        with lock:
            state["in_flight"] += 1
            state["max_in_flight"] = max(state["max_in_flight"], state["in_flight"])
        time.sleep(0.05)
        with lock:
            state["in_flight"] -= 1
        return httpx.Response(200)

    respx.put(SHARED_PUT_URL).mock(side_effect=put_side_effect)

    # No explicit concurrency= — this exercises the documented default of 10.
    _stub_finalize()
    result = _client().context.files.upload_dir(tmp_path, recursive=False)

    assert len(result.uploaded) == total_files
    assert not result.failed
    assert state["max_in_flight"] <= 10
    assert state["max_in_flight"] > 1  # actually overlapping, not serial


# --- async twin (spot check) -------------------------------------------------


@pytest.mark.asyncio
@respx.mock
async def test_async_upload_puts_bytes_and_polls(tmp_path):
    file_path = tmp_path / "report.pdf"
    file_path.write_bytes(b"async content")

    respx.post(f"{BASE}/api/v1/context/files/uploadUrl").mock(
        return_value=httpx.Response(201, json=_slot_json("up-async"))
    )
    respx.put(S3_URL).mock(return_value=httpx.Response(200))
    finalize_route = respx.post(f"{BASE}/api/v1/context/files/up-async/finalize").mock(
        return_value=httpx.Response(201, json=_file_upload_json("up-async", "processing"))
    )
    respx.get(f"{BASE}/api/v1/context/files/up-async").mock(
        return_value=httpx.Response(200, json=_file_upload_json("up-async", "processing"))
    )

    async with AsyncModusManagement(api_key="modus_test_key", base_url=BASE) as client:
        result = await client.context.files.upload(file_path, poll_interval_s=0)

    assert finalize_route.called
    assert result.upload_id == "up-async"
    assert result.status.value == "processing"


@pytest.mark.asyncio
@respx.mock
async def test_async_upload_dir_uploads_all_files_and_continues_on_error(tmp_path):
    (tmp_path / "a.txt").write_text("A")
    (tmp_path / "b.txt").write_text("B")
    (tmp_path / "bad.txt").write_text("bad")

    def upload_urls_side_effect(request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content)
        uploaded = []
        failed = []
        for i, f in enumerate(body["files"]):
            if f["fileName"] == "bad.txt":
                failed.append({"index": i, "fileName": "bad.txt", "error": "not allowed"})
            else:
                uploaded.append(
                    _slot_json(f"async-up-{next(_upload_id_seq)}", upload_url=SHARED_PUT_URL, file_name=f["fileName"])
                )
        return httpx.Response(200, json={"uploaded": uploaded, "failed": failed})

    respx.post(f"{BASE}/api/v1/context/files/uploadUrls").mock(side_effect=upload_urls_side_effect)
    respx.put(SHARED_PUT_URL).mock(return_value=httpx.Response(200))
    respx.get(url__regex=GET_ANY_UPLOAD_ID.pattern).mock(side_effect=_processing_get_side_effect)

    async with AsyncModusManagement(api_key="modus_test_key", base_url=BASE) as client:
        _stub_finalize()
        result = await client.context.files.upload_dir(tmp_path, concurrency=2)

    assert len(result.uploaded) == 2
    assert {u.status.value for u in result.uploaded} == {"processing"}
    assert len(result.failed) == 1
    assert result.failed[0].path.endswith("bad.txt")
    assert result.failed[0].error == "not allowed"


@respx.mock
def test_finalize_sends_file_name_and_returns_resource():
    route = respx.post(f"{BASE}/api/v1/context/files/up-9/finalize").mock(
        return_value=httpx.Response(201, json=_file_upload_json("up-9", "processing"))
    )

    result = _client().context.files.finalize("up-9", file_name="report.pdf")

    assert result.upload_id == "up-9"
    assert json.loads(route.calls[0].request.read()) == {"fileName": "report.pdf"}


@respx.mock
def test_finalize_many_serializes_uploads_and_maps_failures():
    route = respx.post(f"{BASE}/api/v1/context/files/finalize").mock(
        return_value=httpx.Response(
            200,
            json={
                "finalized": [_file_upload_json("up-a", "processing")],
                "failed": [
                    {"index": 1, "uploadId": "up-b", "error": "The upload has not been received."}
                ],
            },
        )
    )

    result = _client().context.files.finalize_many(
        [
            FinalizeInput(upload_id="up-a", file_name="a.pdf"),
            FinalizeInput(upload_id="up-b", file_name="b.pdf"),
        ]
    )

    # Exact wire shape: camelCase keys, request order preserved.
    assert json.loads(route.calls[0].request.read()) == {
        "uploads": [
            {"uploadId": "up-a", "fileName": "a.pdf"},
            {"uploadId": "up-b", "fileName": "b.pdf"},
        ]
    }
    assert [f.upload_id for f in result.finalized] == ["up-a"]
    assert result.failed[0].index == 1
    assert result.failed[0].upload_id == "up-b"


def test_finalize_many_rejects_an_empty_batch():
    with pytest.raises(ValueError):
        _client().context.files.finalize_many([])


def test_finalize_many_rejects_a_batch_over_the_cap():
    uploads = [
        FinalizeInput(upload_id=f"u-{i}", file_name=f"f-{i}.pdf")
        for i in range(MAX_BULK_UPLOAD_FILES + 1)
    ]
    with pytest.raises(ValueError):
        _client().context.files.finalize_many(uploads)


@respx.mock
def test_upload_files_uploads_an_explicit_list(tmp_path):
    a = tmp_path / "a.txt"
    a.write_text("A")
    b = tmp_path / "b.txt"
    b.write_text("B")

    respx.post(f"{BASE}/api/v1/context/files/uploadUrls").mock(
        return_value=httpx.Response(
            200,
            json={
                "uploaded": [_slot_json("up-a", upload_url=S3_URL), _slot_json("up-b", upload_url=S3_URL)],
                "failed": [],
            },
        )
    )
    respx.put(S3_URL).mock(return_value=httpx.Response(200))
    _stub_finalize()

    result = _client().context.files.upload_files([a, b])

    assert len(result.uploaded) == 2
    assert not result.failed


@respx.mock
def test_upload_files_on_progress_reports_completed_and_total(tmp_path):
    a = tmp_path / "a.txt"
    a.write_text("A")
    b = tmp_path / "b.txt"
    b.write_text("B")

    respx.post(f"{BASE}/api/v1/context/files/uploadUrls").mock(
        return_value=httpx.Response(
            200,
            json={
                "uploaded": [_slot_json("up-a", upload_url=S3_URL), _slot_json("up-b", upload_url=S3_URL)],
                "failed": [],
            },
        )
    )
    respx.put(S3_URL).mock(return_value=httpx.Response(200))
    _stub_finalize()

    ticks: list = []
    result = _client().context.files.upload_files(
        [a, b],
        on_progress=lambda p: ticks.append((p.completed, p.total, p.succeeded, p.failed)),
    )

    assert len(result.uploaded) == 2
    assert ticks == [(1, 2, 1, 0), (2, 2, 2, 0)]


@respx.mock
def test_upload_dir_on_progress_counts_slot_failures(tmp_path):
    (tmp_path / "good.txt").write_text("ok")
    (tmp_path / "bad.txt").write_text("bad")

    respx.post(f"{BASE}/api/v1/context/files/uploadUrls").mock(
        return_value=httpx.Response(
            200,
            json={
                "uploaded": [_slot_json("up-good")],
                "failed": [{"index": 0, "fileName": "bad.txt", "error": "not allowed"}],
            },
        )
    )
    respx.put(S3_URL).mock(return_value=httpx.Response(200))
    _stub_finalize()

    ticks: list = []
    result = _client().context.files.upload_dir(
        tmp_path,
        on_progress=lambda p: ticks.append((p.completed, p.total, p.succeeded, p.failed)),
    )

    assert len(result.uploaded) == 1
    assert len(result.failed) == 1
    assert ticks == [(1, 2, 0, 1), (2, 2, 1, 1)]


@respx.mock
def test_upload_files_maps_a_finalize_failure_back_to_its_local_path(tmp_path):
    a = tmp_path / "a.txt"
    a.write_text("A")

    respx.post(f"{BASE}/api/v1/context/files/uploadUrls").mock(
        return_value=httpx.Response(
            200, json={"uploaded": [_slot_json("up-a", upload_url=S3_URL)], "failed": []}
        )
    )
    respx.put(S3_URL).mock(return_value=httpx.Response(200))
    respx.post(f"{BASE}/api/v1/context/files/finalize").mock(
        return_value=httpx.Response(
            200,
            json={
                "finalized": [],
                "failed": [{"index": 0, "uploadId": "up-a", "error": "not received"}],
            },
        )
    )

    result = _client().context.files.upload_files([a])

    assert not result.uploaded
    assert result.failed[0].path == str(a)
    assert result.failed[0].error == "not received"


@pytest.mark.asyncio
@respx.mock
async def test_async_finalize_and_finalize_many():
    respx.post(f"{BASE}/api/v1/context/files/up-9/finalize").mock(
        return_value=httpx.Response(201, json=_file_upload_json("up-9", "processing"))
    )
    bulk = respx.post(f"{BASE}/api/v1/context/files/finalize").mock(
        return_value=httpx.Response(
            200, json={"finalized": [_file_upload_json("up-a", "processing")], "failed": []}
        )
    )

    async with AsyncModusManagement(api_key="modus_test_key", base_url=BASE) as client:
        one = await client.context.files.finalize("up-9", file_name="report.pdf")
        many = await client.context.files.finalize_many(
            [FinalizeInput(upload_id="up-a", file_name="a.pdf")]
        )

    assert one.upload_id == "up-9"
    assert [f.upload_id for f in many.finalized] == ["up-a"]
    assert json.loads(bulk.calls[0].request.read())["uploads"][0]["fileName"] == "a.pdf"
