"""Enforce context creator pairing and read accessor exports."""

from __future__ import annotations

import importlib

import modus
from modus.management.resources.context.context import AsyncContextResource, ContextResource

from .context_ergonomics_manifest import (
    CREATOR_UPDATE_PAIRS,
    READ_ACCESSORS,
    SHARED_READ_ACCESSORS,
)


def test_creator_update_pairs_exist_on_context_resource() -> None:
    for _kind, (create_name, update_name) in CREATOR_UPDATE_PAIRS.items():
        assert hasattr(ContextResource, create_name), f"missing ContextResource.{create_name}"
        assert hasattr(ContextResource, update_name), f"missing ContextResource.{update_name}"
        assert hasattr(AsyncContextResource, create_name)
        assert hasattr(AsyncContextResource, update_name)


def test_read_accessors_exported_from_modus() -> None:
    accessors = importlib.import_module("modus.types.context_accessors")
    for names in READ_ACCESSORS.values():
        for name in names:
            assert hasattr(accessors, name)
            assert hasattr(modus, name)
    for name in SHARED_READ_ACCESSORS:
        assert hasattr(accessors, name)
        assert hasattr(modus, name)
