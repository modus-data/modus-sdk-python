"""Dashboard models accept real service payloads and keep every field they carry.

The fixtures under ``tests/fixtures/dashboards`` are sanitized responses captured from
the running service, so they include stored shapes that hand-written fixtures miss.
"""

import json
from pathlib import Path

import pytest
from modus.management.types.context_dashboards import (
    Dashboard,
    DashboardElementResult,
    DashboardElementsList,
)
from pydantic import BaseModel

FIXTURES = Path(__file__).resolve().parents[2] / "fixtures" / "dashboards"


@pytest.mark.parametrize(
    ("fixture", "model"),
    [
        ("dashboard.json", Dashboard),
        ("elements-list.json", DashboardElementsList),
        ("element-filter.json", DashboardElementResult),
        ("element-filter-date-range.json", DashboardElementResult),
        ("element-filter-number.json", DashboardElementResult),
        ("element-tile.json", DashboardElementResult),
        ("element-tile-chart.json", DashboardElementResult),
    ],
)
def test_live_payload_round_trips(fixture: str, model: type[BaseModel]) -> None:
    payload = json.loads((FIXTURES / fixture).read_text())
    parsed = model.model_validate(payload)
    assert parsed.model_dump(mode="json", by_alias=True, exclude_unset=True) == payload
