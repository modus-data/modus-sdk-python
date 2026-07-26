"""Tool catalog types (re-exported from ListToolsResponseDto)."""

from modus._generated.models import (
    ListToolsResponseDto,
    ToolCatalogActionDto,
    ToolCatalogEntryDto,
)

ToolCatalogAction = ToolCatalogActionDto
ToolCatalogEntry = ToolCatalogEntryDto
ListToolsResponse = ListToolsResponseDto

__all__ = ["ToolCatalogAction", "ToolCatalogEntry", "ListToolsResponse"]
