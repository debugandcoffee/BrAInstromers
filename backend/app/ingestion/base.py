from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime, timezone

import requests

from app.config import settings
from app.ingestion.chunking import chunk_text
from app.models import RawDocument
from app.storage.document_store import DocumentStore


class SourceAdapter(ABC):
    source: str

    def __init__(self, store: DocumentStore):
        self.store = store
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": settings.user_agent})

    @abstractmethod
    def fetch(self, query: str, limit: int = 10) -> list[RawDocument]:
        raise NotImplementedError

    def ingest(self, query: str, limit: int = 10) -> dict[str, int | str]:
        started_at = datetime.now(timezone.utc)
        seen = 0
        changed = 0
        try:
            documents = self.fetch(query, limit=limit)
            for document in documents:
                seen += 1
                document_id, did_change = self.store.upsert_document(document)
                if did_change:
                    changed += 1
                chunks = [
                    (
                        text,
                        {
                            "source": document.source,
                            "external_id": document.external_id,
                            "title": document.title,
                            "url": document.url,
                        },
                    )
                    for text in chunk_text(document.text)
                ]
                self.store.replace_chunks(document_id, chunks)

            self.store.record_run(self.source, query, "ok", seen, changed, started_at)
            return {"source": self.source, "seen": seen, "changed": changed}
        except Exception as exc:
            self.store.record_run(self.source, query, "error", seen, changed, started_at, str(exc))
            raise
