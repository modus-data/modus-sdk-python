"""Search and manage long-term memories for a scope."""

from __future__ import annotations

from modus._generated.resources.management.scopes.memories import (
    _AsyncScopesMemoriesResourceBase,
    _ScopesMemoriesResourceBase,
)


class ScopeMemoriesResource(_ScopesMemoriesResourceBase):
    """Long-term memory stored per scope."""


class AsyncScopeMemoriesResource(_AsyncScopesMemoriesResourceBase):
    """Long-term memory stored per scope (async)."""
