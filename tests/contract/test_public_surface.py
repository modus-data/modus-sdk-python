"""
Snapshot test for the SDK's reachable public method surface.

Failures mean a later refactor (moving resource methods into generated base classes)
changed the public surface. Regenerate intentionally with:
    cd distribution/clients/python/modus-sdk
    bash ../../../../scripts/sdk-python/ensure-uv.sh run python ../scripts/emit_public_surface.py --write
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import pytest

TEST_DIR = Path(__file__).resolve().parent
SNAPSHOT_PATH = TEST_DIR.parent / "snapshots" / "public_surface.json"
SCRIPTS_DIR = TEST_DIR.parents[2] / "scripts"

sys.path.insert(0, str(SCRIPTS_DIR))
from emit_public_surface import emit_public_surface, walk_public_surface  # noqa: E402


def _accept_all(value: object) -> type:
    """Permissive `is_reachable_class` for fixture walks: every object is in scope."""
    return value if isinstance(value, type) else type(value)


def test_matches_committed_snapshot():
    if not SNAPSHOT_PATH.exists():
        pytest.fail(
            f"Snapshot missing: {SNAPSHOT_PATH}. Run:\n"
            "  cd distribution/clients/python/modus-sdk\n"
            "  bash ../../../../scripts/sdk-python/ensure-uv.sh run python "
            "../scripts/emit_public_surface.py --write"
        )
    committed = json.loads(SNAPSHOT_PATH.read_text())
    assert emit_public_surface() == committed


def test_reaches_bound_and_async_resources():
    keys = set(emit_public_surface().keys())
    assert "ScopeMemoriesResource.update" in keys
    assert "AsyncScopeMemoriesResource.update" in keys
    assert "ConnectionsResource.find" in keys


def test_no_leaked_absolute_paths_or_addresses():
    """Deterministic across machines: no filesystem path, no object repr address."""
    leak_pattern = re.compile(r"/Users/|/home/|[A-Za-z]:\\\\|0x[0-9a-fA-F]+")
    leaked = [
        (key, value) for key, value in emit_public_surface().items() if leak_pattern.search(value)
    ]
    assert leaked == []


def _two_dup_roots(*, second_has_get: bool) -> list:
    """
    Two different classes, both named `Dup`, both with an identical `other`, and
    (unless `second_has_get` is False) an identical `get` too — so the only possible
    difference between the two scenarios is a pure deletion of `get` from the second
    class, nothing added or renamed.
    """

    class RootA:
        def __init__(self) -> None:
            class Dup:
                def get(self) -> str:
                    return "a"

                def other(self) -> str:
                    return "shared"

            self.dup = Dup()

    class RootB:
        def __init__(self) -> None:
            if second_has_get:

                class Dup:
                    def get(self) -> str:
                        return "a"  # identical signature to RootA's Dup.get

                    def other(self) -> str:
                        return "shared"
            else:

                class Dup:
                    def other(self) -> str:
                        return "shared"

            self.dup = Dup()

    return [RootA(), RootB()]


def test_same_named_classes_qualify_even_when_signatures_agree():
    surface = walk_public_surface(_two_dup_roots(second_has_get=True), is_reachable_class=_accept_all)
    assert "Dup.get" not in surface
    assert "Dup.other" not in surface
    assert sum(1 for key in surface if key.endswith(".Dup.get")) == 2
    assert sum(1 for key in surface if key.endswith(".Dup.other")) == 2


def test_deleting_a_method_from_one_same_named_class_changes_the_snapshot():
    """
    Controller ruling: two same-named classes always key by full module path, even when
    every member they share agrees — otherwise one class losing a method it shared with
    its same-named sibling can leave the snapshot byte-identical (verified: this failed
    before the fix, since the two `Dup.get` entries collapsed to one shared plain key).
    """
    before = walk_public_surface(_two_dup_roots(second_has_get=True), is_reachable_class=_accept_all)
    after = walk_public_surface(_two_dup_roots(second_has_get=False), is_reachable_class=_accept_all)
    assert before != after


def test_unresolvable_return_annotation_fails_loudly_with_context():
    class Broken:
        def get(self) -> DoesNotExistAnywhere:  # noqa: F821
            raise NotImplementedError

    class Root:
        def __init__(self) -> None:
            self.broken = Broken()

    with pytest.raises(RuntimeError, match=r"Broken\.get") as excinfo:
        walk_public_surface([Root()], is_reachable_class=_accept_all)
    assert isinstance(excinfo.value.__cause__, NameError)


# Module-level (not function-nested, unlike `_two_dup_roots`'s fixtures): a quoted
# forward ref resolves in `fn.__module__`'s globals, so the referenced class actually
# has to live there, matching how real SDK resource classes are always module-level.
class _QuotedChild:
    def hello(self) -> str:
        return "hi"


class _QuotedParent:
    def get(self) -> "_QuotedChild":
        raise NotImplementedError


class _QuotedParentRoot:
    def __init__(self) -> None:
        self.parent = _QuotedParent()


class _QuotedMissingParent:
    def get(self) -> "DoesNotExistQuotedOrNot":  # noqa: F821
        raise NotImplementedError


class _QuotedMissingRoot:
    def __init__(self) -> None:
        self.parent = _QuotedMissingParent()


def test_quoted_return_annotation_is_traversed():
    """
    A valid, quoted forward ref (`-> "_QuotedChild"`) must resolve to the class and be
    walked, not just the bare, unquoted form `test_reaches_bound_and_async_resources`
    already covers via the real SDK's factory methods.
    """
    surface = walk_public_surface([_QuotedParentRoot()], is_reachable_class=_accept_all)
    assert "_QuotedChild.hello" in surface


def test_quoted_unresolvable_return_annotation_fails_loudly_with_context():
    with pytest.raises(RuntimeError, match=r"_QuotedMissingParent\.get") as excinfo:
        walk_public_surface([_QuotedMissingRoot()], is_reachable_class=_accept_all)
    assert isinstance(excinfo.value.__cause__, NameError)


class _AnnotationFirstResource:
    def read(self) -> str:
        return "resource"


class _AnnotationFirstChild:
    def __init__(self) -> None:
        self.resource = _AnnotationFirstResource()


def test_instance_attributes_are_walked_after_annotation_discovery():
    class Root:
        def __init__(self) -> None:
            self.child = _AnnotationFirstChild()

        def get_child(self) -> _AnnotationFirstChild:
            return self.child

    surface = walk_public_surface([Root()], is_reachable_class=_accept_all)
    assert "_AnnotationFirstResource.read" in surface


def test_classmethods_and_staticmethods_are_included_without_properties():
    class Resource:
        @classmethod
        def get(cls, key: str) -> str:
            return key

        @staticmethod
        def exists(key: str) -> bool:
            return bool(key)

        @property
        def status(self) -> str:
            raise AssertionError("properties must not be evaluated")

    class Root:
        def __init__(self) -> None:
            self.resource = Resource()

    surface = walk_public_surface([Root()], is_reachable_class=_accept_all)
    assert surface == {
        "Resource.exists": "(key: 'str') -> 'bool'",
        "Resource.get": "(cls, key: 'str') -> 'str'",
    }
