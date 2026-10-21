"""Manage subordinate scopes supervised by a scope."""

from modus._generated.resources.management.scopes.supervision import (
    _AsyncScopesSupervisionResourceBase,
    _ScopesSupervisionResourceBase,
)


class ScopeSupervisionResource(_ScopesSupervisionResourceBase):
    """Manage subordinate scopes supervised by a scope."""


class AsyncScopeSupervisionResource(_AsyncScopesSupervisionResourceBase):
    """Asynchronously manage subordinate scopes supervised by a scope."""
