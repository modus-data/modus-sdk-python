"""Completed evaluation runs parse into typed models.

The bodies are the bytes staging returned for ``GET /api/v1/scopes/68/evaluations/runs[/{runId}]``
on 2026-10-25, except ``startedAt``/``finishedAt``: staging still sent JS ``Date.toString()``
there, and the server now sends the same instants as ISO 8601.
"""

import json
from datetime import datetime, timezone

import httpx
import respx

BASE = "https://api.modus.com"
RUN = json.loads(
    '{"id":"ea8cba35-532f-4f3f-bb34-b81bb35c3a13","skillId":68,"trigger":"manual","status":"completed",'
    '"startedAt":"2026-10-25T14:38:43.000Z","finishedAt":"2026-10-25T14:38:45.000Z",'
    '"totalCases":1,"passedCases":1,"failedCases":0,"avgScore":100,"isRegression":false,'
    '"judgeModel":"openai/gpt-oss-120b","errorMessage":null,"results":[{"id":"f6c2d78b-1a3f-41c8-83f8-8b23c4e79b9e",'
    '"caseId":"c1","task":"Reply with the single word: hi","expectedOutput":"hi","actualOutput":"hi",'
    '"passed":true,"score":100,"reasoning":"The response exactly matches the expected single word \'hi\'.",'
    '"wasPassingBefore":null}]}'
)


@respx.mock
def test_list_runs_parses_a_completed_run(client):
    listed = {k: v for k, v in RUN.items() if k != "results"}
    respx.get(f"{BASE}/api/v1/scopes/68/evaluations/runs").mock(
        return_value=httpx.Response(200, json={"runs": [listed], "nextPageToken": None})
    )
    [run] = list(client.scopes.evaluations(68).list_runs())
    assert run.avg_score == 100
    assert run.finished_at == datetime(2026, 10, 25, 14, 38, 45, tzinfo=timezone.utc)


@respx.mock
def test_get_run_parses_a_completed_run_with_results(client):
    respx.get(f"{BASE}/api/v1/scopes/68/evaluations/runs/{RUN['id']}").mock(
        return_value=httpx.Response(200, json=RUN)
    )
    run = client.scopes.evaluations(68).get_run(RUN["id"])
    [result] = run.results
    assert (result.score, result.passed, result.actual_output) == (100, True, "hi")
    assert result.was_passing_before is None
    assert run.started_at == datetime(2026, 10, 25, 14, 38, 43, tzinfo=timezone.utc)
