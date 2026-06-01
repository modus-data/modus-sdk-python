"""Context (knowledge base) types for modus.management."""

from __future__ import annotations

from datetime import datetime
from typing import Any, List, Literal, Optional

from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel

ContextType = Literal[
    "note", "saved_query", "metric", "fact", "filter", "link", "dimension",
    "salesforce_object_field", "looker_explore", "dbt_model",
    "bigquery_table", "snowflake_table", "databricks_table",
    "postgresql_table", "clickhouse_table",
]


class ContextItem(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True, extra="ignore")
    uid: str
    context_type: str
    title: Optional[str] = None
    description: Optional[str] = None
    content: Optional[Any] = None
    verification_status: Optional[str] = None
    user_feedback: Optional[str] = None
    topics: Optional[List[str]] = None
    connection_id: Optional[str] = None
    update_source: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class CreatedContextItem(BaseModel):
    """Returned by all POST /api/v1/context/* creator endpoints."""
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True, extra="ignore")
    context_item_id: str
    kind: str
    title: str
    s3_key: str


class ContextItemUpdate(BaseModel):
    """Fields that can be updated on an existing context item."""
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True, extra="ignore")
    title: Optional[str] = None
    description: Optional[str] = None
    content: Optional[Any] = None
    verification_status: Optional[str] = None


class ContextItemDeletion(BaseModel):
    """Returned by DELETE /api/v1/context/items/:uid."""
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True, extra="ignore")
    uid: str
    context_type: str
