"""Documented usage type-checks under ``mypy --strict``, with no casts.

Each snippet failed before its fix:
- ``event.type`` was ``str``, so ``if event.type == "token": event.content`` did not narrow
  (``"ErrorEvent" has no attribute "content"``) in every documented stream loop.
- ``modus.management`` was not re-exported, so ``import modus; modus.management.ModusManagement()``
  (the docstrings' form) was ``Module has no attribute "management"``.
- ``workflows.create`` took only the ``AgentType`` enum, so the docstring's
  ``create("Daily report", "workflow")`` was an ``arg-type`` error.
- ``context_item_label`` took only ``ContextItem``, so the ``lookup()`` docstring's
  ``context_item_label(found)`` was an ``arg-type`` error.
"""

from __future__ import annotations

import pytest
from mypy import api as mypy_api

SNIPPETS = {
    "event type narrows": (
        "from typing import Iterable\n"
        "from modus.types.runs import RunEvent\n"
        "def text(events: Iterable[RunEvent]) -> str:\n"
        "    out = ''\n"
        "    for event in events:\n"
        "        if event.type == 'token':\n"
        "            out += event.content\n"
        "        elif event.type == 'done':\n"
        "            out += event.run_id\n"
        "    return out\n"
    ),
    "modus.management attribute": (
        "import modus\n"
        "def mgmt() -> modus.management.ModusManagement:\n"
        "    return modus.management.ModusManagement(api_key='k')\n"
    ),
    "workflow type as a string": (
        "from modus.management import ModusManagement\n"
        "def create(mgmt: ModusManagement) -> int:\n"
        "    return mgmt.workflows.create('Daily report', 'workflow').id\n"
    ),
    "label of a lookup row": (
        "import modus\n"
        "def label(client: modus.Modus) -> str:\n"
        "    found = client.context.items.lookup('note', ['finance', 'arr-definition'])\n"
        "    return modus.context_item_label(found) if found else ''\n"
    ),
}


@pytest.mark.parametrize("snippet", SNIPPETS.values(), ids=SNIPPETS.keys())
def test_snippet_typechecks_under_mypy_strict(snippet: str) -> None:
    stdout, stderr, status = mypy_api.run(
        ["--strict", "--follow-imports=silent", "--no-incremental", "-c", snippet]
    )
    assert status == 0, stdout + stderr
