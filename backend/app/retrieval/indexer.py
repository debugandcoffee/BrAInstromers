from __future__ import annotations

from BrAInstromers.backend.app.config import settings
from BrAInstromers.backend.app.retrieval.embeddings import EmbeddingModel
from BrAInstromers.backend.app.storage.document_store import DocumentStore


def build_lexical_index(store: DocumentStore) -> int:
    return store.rebuild_fts()


def build_semantic_index(
    store: DocumentStore,
    model_name: str = settings.embedding_model,
    batch_size: int = 32,
    limit: int = 1000,
) -> dict[str, int | str]:
    embedder = EmbeddingModel(model_name)
    indexed = 0

    while True:
        rows = store.chunks_without_embedding(model_name, limit=limit)
        if not rows:
            break

        for start in range(0, len(rows), batch_size):
            batch = rows[start : start + batch_size]
            vectors = embedder.encode_passages([row["text"] for row in batch])
            for row, vector in zip(batch, vectors):
                store.upsert_embedding(int(row["id"]), model_name, vector)
                indexed += 1

        if len(rows) < limit:
            break

    return {"model": model_name, "indexed": indexed}
