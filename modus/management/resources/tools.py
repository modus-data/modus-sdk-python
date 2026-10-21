"""Tool catalog resource."""

from __future__ import annotations

from modus._generated.resources.management.tools import (
    _AsyncToolsResourceBase,
    _ToolsResourceBase,
)


class ToolsResource(_ToolsResourceBase):
    """Browse the catalog of tool/integration surfaces a scope can select in its toolset."""


class AsyncToolsResource(_AsyncToolsResourceBase):
    """Browse the catalog of tool/integration surfaces a scope can select in its toolset (async)."""
