"""Public types for integration connections."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class Connection:
    """A warehouse or SaaS integration connection in the organisation."""

    id: str
    name: Optional[str]
    type: Optional[str]
