"""Context item content blobs matching modus-api creators.service.ts shapes."""

from __future__ import annotations

from typing import Any

NOTE_CONTENT: dict[str, Any] = {
    "title": "Fiscal Year",
    "content": "Feb 1 – Jan 31.",
    "s3Key": "context_notes/note-id/Fiscal_Year.md",
    "noteId": "note-id-001",
    "sizeBytes": 16,
    "createdAt": "2026-01-01T00:00:00.000Z",
}

LINK_CONTENT: dict[str, Any] = {
    "title": "Python json docs",
    "url": "https://docs.python.org/3/library/json.html",
    "linkId": "link-id-001",
    "isCrawl": False,
    "pageCount": 1,
    "s3Key": "context_links/link-id-001/Python_json_docs.md",
    "parsedContentLocation": "s3",
    "contentSize": 1024,
    "extractedAt": "2026-01-01T00:00:00.000Z",
    "createdAt": "2026-01-01T00:00:00.000Z",
}

SAVED_QUERY_CONTENT: dict[str, Any] = {
    "name": "Top Customers",
    "query": "SELECT id FROM customers LIMIT 10",
    "queryId": "query-id-001",
    "s3Key": "context_queries/query-id-001/Top_Customers.sql",
    "connectionId": "conn-001",
    "path": ["analytics", "public"],
    "sizeBytes": 32,
    "createdAt": "2026-01-01T00:00:00.000Z",
}
