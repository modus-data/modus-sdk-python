"""
Context (knowledge base) types.

Context items are pieces of knowledge that skills use to answer questions —
notes, saved queries, metrics, facts, filters, links, and dimensions.

Matches the ContextItemDto shape from GET /api/v1/context/items.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel

ContextType = Literal[
    "note",
    "saved_query",
    "metric",
    "fact",
    "filter",
    "link",
    "dimension",
    # Integration-synced types:
    "salesforce_object_field",
    "looker_explore",
    "dbt_model",
    "bigquery_table",
    "snowflake_table",
    "databricks_table",
    "postgresql_table",
    "clickhouse_table",
]

VerificationStatus = Literal["verified", "unverified", "needs_review"]
UserFeedback = Literal["positive", "negative", "none"]


class ContextItem(BaseModel):
    """
    A single item in the Modus knowledge base.

    Context items are the knowledge layer that skills draw on when
    answering questions. They can be created manually (notes, metrics,
    saved queries) or synced automatically from connected data sources.
    """

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    uid: str
    context_type: str
    title: Optional[str] = None
    description: Optional[str] = None
    content: Optional[Any] = None
    """Polymorphic body (note text, saved-query fields, etc.) — shape depends on ``context_type``."""
    verification_status: Optional[str] = None
    user_feedback: Optional[str] = None
    topics: Optional[List[str]] = None
    connection_id: Optional[str] = None
    selection_id: Optional[str] = None
    org_id: Optional[str] = None
    data_path: Optional[List[str]] = None
    last_update_metadata: Optional[Dict[str, Any]] = None
    update_source: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class CreatedContextItem(BaseModel):
    """
    Response returned by all POST /api/v1/context/* creator endpoints.

    This is a lightweight envelope — it confirms creation and provides the
    new item's UID. Call client.context.items.get(item.context_item_id) for
    the full ContextItem.
    """

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    context_item_id: str
    """The UUID of the newly created context item."""

    kind: str
    """Context type string e.g. 'note', 'saved_query', 'link'."""

    title: str
    """The title that was stored."""

    s3_key: str
    """Internal S3 object key where the content is stored."""


class ContextItemUpdate(BaseModel):
    """Fields that can be updated on an existing context item."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    title: Optional[str] = None
    description: Optional[str] = None
    content: Optional[Any] = None  # string, dict, or list — matches ContextItem.content
    verification_status: Optional[str] = None


class ContextItemDeletion(BaseModel):
    """
    Returned by client.context.items.delete(uid).
    Mirrors the 200 response body from DELETE /api/v1/context/items/:uid.
    """

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    uid: str
    context_type: str
