"""Supervision get takes active or draft, not the scope published view."""

from __future__ import annotations

from pathlib import Path
from typing import get_args

from modus.types.views import SupervisionView, VariationView


def test_supervision_view_is_active_or_draft() -> None:
    assert get_args(SupervisionView) == ("active", "draft")
    assert "published" in get_args(VariationView)
    assert "published" not in get_args(SupervisionView)


def test_supervision_get_uses_supervision_view() -> None:
    source = (
        Path(__file__).resolve().parents[1]
        / "modus/_generated/resources/management/scopes/supervision.py"
    ).read_text(encoding="utf-8")
    assert "SupervisionView" in source
    assert "VariationView" not in source
