"""Tests for modus._deprecation.warn_deprecated."""

from __future__ import annotations

import warnings

import pytest
from modus._deprecation import warn_deprecated


def test_warn_deprecated_emits_deprecation_warning() -> None:
    with pytest.warns(DeprecationWarning, match="legacy.list.*scopes.list"):
        warn_deprecated(old="legacy.list", new="scopes.list")


def test_warn_deprecated_message_names_next_release() -> None:
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always", DeprecationWarning)
        warn_deprecated(old="a", new="b")
    assert len(caught) == 1
    assert "next release" in str(caught[0].message)
