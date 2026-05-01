from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass(frozen=True)
class RawDocument:
    source: str
    external_id: str
    title: str
    text: str
    url: str | None = None
    published_at: str | None = None
    updated_at: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    fetched_at: datetime = field(default_factory=utc_now)


@dataclass(frozen=True)
class PreparedChunk:
    document_key: str
    chunk_index: int
    text: str
    metadata: dict[str, Any] = field(default_factory=dict)
