from __future__ import annotations

import hashlib
import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator

from app.models import RawDocument


SCHEMA = """
CREATE TABLE IF NOT EXISTS documents (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  source TEXT NOT NULL,
  external_id TEXT NOT NULL,
  title TEXT NOT NULL,
  url TEXT,
  text TEXT NOT NULL,
  metadata_json TEXT NOT NULL,
  content_hash TEXT NOT NULL,
  published_at TEXT,
  updated_at TEXT,
  fetched_at TEXT NOT NULL,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE(source, external_id)
);

CREATE TABLE IF NOT EXISTS chunks (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  document_id INTEGER NOT NULL,
  chunk_index INTEGER NOT NULL,
  text TEXT NOT NULL,
  metadata_json TEXT NOT NULL,
  token_estimate INTEGER NOT NULL,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE(document_id, chunk_index),
  FOREIGN KEY(document_id) REFERENCES documents(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS chunk_embeddings (
  chunk_id INTEGER PRIMARY KEY,
  model TEXT NOT NULL,
  vector_json TEXT NOT NULL,
  dimension INTEGER NOT NULL,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY(chunk_id) REFERENCES chunks(id) ON DELETE CASCADE
);

CREATE VIRTUAL TABLE IF NOT EXISTS chunk_fts USING fts5(
  text,
  title,
  source,
  content='',
  tokenize='unicode61 remove_diacritics 2'
);

CREATE TABLE IF NOT EXISTS ingestion_runs (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  source TEXT NOT NULL,
  query TEXT,
  status TEXT NOT NULL,
  documents_seen INTEGER NOT NULL DEFAULT 0,
  documents_changed INTEGER NOT NULL DEFAULT 0,
  error TEXT,
  started_at TEXT NOT NULL,
  finished_at TEXT NOT NULL
);
"""


class DocumentStore:
    def __init__(self, db_path: Path):
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        #sqlite3.enable_callback_tracebacks(True)

    @contextmanager
    def connect(self) -> Iterator[sqlite3.Connection]:
        connection = sqlite3.connect(self.db_path)
        #connection.set_trace_callback(print)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        try:
            yield connection
            connection.commit()
        finally:
            connection.close()

    def init_db(self) -> None:
        with self.connect() as connection:
            connection.executescript(SCHEMA)

    def upsert_document(self, document: RawDocument) -> tuple[int, bool]:
        self.init_db()
        content_hash = self._hash_text(document.text)
        fetched_at = document.fetched_at.astimezone(timezone.utc).isoformat()
        metadata_json = json.dumps(document.metadata, ensure_ascii=False, sort_keys=True)

        with self.connect() as connection:
            existing = connection.execute(
                "SELECT id, content_hash FROM documents WHERE source = ? AND external_id = ?",
                (document.source, document.external_id),
            ).fetchone()

            if existing:
                changed = existing["content_hash"] != content_hash
                connection.execute(
                    """
                    UPDATE documents
                    SET title = ?, url = ?, text = ?, metadata_json = ?, content_hash = ?,
                        published_at = ?, updated_at = ?, fetched_at = ?
                    WHERE id = ?
                    """,
                    (
                        document.title,
                        document.url,
                        document.text,
                        metadata_json,
                        content_hash,
                        document.published_at,
                        document.updated_at,
                        fetched_at,
                        existing["id"],
                    ),
                )
                return int(existing["id"]), changed

            cursor = connection.execute(
                """
                INSERT INTO documents (
                  source, external_id, title, url, text, metadata_json, content_hash,
                  published_at, updated_at, fetched_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    document.source,
                    document.external_id,
                    document.title,
                    document.url,
                    document.text,
                    metadata_json,
                    content_hash,
                    document.published_at,
                    document.updated_at,
                    fetched_at,
                ),
            )
            return int(cursor.lastrowid), True

    def replace_chunks(self, document_id: int, chunks: list[tuple[str, dict]]) -> None:
        with self.connect() as connection:
            existing = connection.execute(
                "SELECT id FROM chunks WHERE document_id = ?",
                (document_id,),
            ).fetchall()
            for row in existing:
                connection.execute("DELETE FROM chunk_fts WHERE rowid = ?", (row["id"],))
            connection.execute("DELETE FROM chunks WHERE document_id = ?", (document_id,))
            for index, (text, metadata) in enumerate(chunks):
                cursor = connection.execute(
                    """
                    INSERT INTO chunks (document_id, chunk_index, text, metadata_json, token_estimate)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        document_id,
                        index,
                        text,
                        json.dumps(metadata, ensure_ascii=False, sort_keys=True),
                        max(1, len(text) // 4),
                    ),
                )
                chunk_id = int(cursor.lastrowid)
                connection.execute(
                    "INSERT INTO chunk_fts(rowid, text, title, source) VALUES (?, ?, ?, ?)",
                    (
                        chunk_id,
                        text,
                        str(metadata.get("title", "")),
                        str(metadata.get("source", "")),
                    ),
                )

    def record_run(
        self,
        source: str,
        query: str | None,
        status: str,
        documents_seen: int,
        documents_changed: int,
        started_at: datetime,
        error: str | None = None,
    ) -> None:
        finished_at = datetime.now(timezone.utc)
        with self.connect() as connection:
            connection.execute(
                """
                INSERT INTO ingestion_runs (
                  source, query, status, documents_seen, documents_changed, error,
                  started_at, finished_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    source,
                    query,
                    status,
                    documents_seen,
                    documents_changed,
                    error,
                    started_at.isoformat(),
                    finished_at.isoformat(),
                ),
            )

    def stats(self) -> dict[str, int]:
        self.init_db()
        with self.connect() as connection:
            documents = connection.execute("SELECT COUNT(*) AS count FROM documents").fetchone()["count"]
            chunks = connection.execute("SELECT COUNT(*) AS count FROM chunks").fetchone()["count"]
            embeddings = connection.execute("SELECT COUNT(*) AS count FROM chunk_embeddings").fetchone()["count"]
            runs = connection.execute("SELECT COUNT(*) AS count FROM ingestion_runs").fetchone()["count"]
        return {
            "documents": int(documents),
            "chunks": int(chunks),
            "embeddings": int(embeddings),
            "ingestion_runs": int(runs),
        }

    def list_documents(self, limit: int = 20) -> list[dict]:
        self.init_db()
        with self.connect() as connection:
            rows = connection.execute(
                """
                SELECT id, source, external_id, title, url, fetched_at, published_at,
                       substr(text, 1, 500) AS preview
                FROM documents
                ORDER BY fetched_at DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
        return [dict(row) for row in rows]

    def list_chunks(self, limit: int = 20) -> list[dict]:
        self.init_db()
        with self.connect() as connection:
            rows = connection.execute(
                """
                SELECT chunks.id, documents.source, documents.title, chunks.chunk_index,
                       substr(chunks.text, 1, 700) AS preview
                FROM chunks
                JOIN documents ON documents.id = chunks.document_id
                ORDER BY chunks.created_at DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
        return [dict(row) for row in rows]

    def chunks_without_embedding(self, model: str, limit: int = 500) -> list[dict]:
        self.init_db()
        with self.connect() as connection:
            rows = connection.execute(
                """
                SELECT chunks.id, chunks.text, documents.title, documents.source, documents.url,
                       documents.external_id, chunks.chunk_index
                FROM chunks
                JOIN documents ON documents.id = chunks.document_id
                LEFT JOIN chunk_embeddings
                  ON chunk_embeddings.chunk_id = chunks.id
                 AND chunk_embeddings.model = ?
                WHERE chunk_embeddings.chunk_id IS NULL
                ORDER BY chunks.id
                LIMIT ?
                """,
                (model, limit),
            ).fetchall()
        return [dict(row) for row in rows]

    def upsert_embedding(self, chunk_id: int, model: str, vector: list[float]) -> None:
        with self.connect() as connection:
            connection.execute(
                """
                INSERT INTO chunk_embeddings (chunk_id, model, vector_json, dimension)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(chunk_id) DO UPDATE SET
                  model = excluded.model,
                  vector_json = excluded.vector_json,
                  dimension = excluded.dimension,
                  created_at = CURRENT_TIMESTAMP
                """,
                (chunk_id, model, json.dumps(vector), len(vector)),
            )

    def semantic_candidates(self, model: str, limit: int | None = None) -> list[dict]:
        self.init_db()
        sql = """
            SELECT chunks.id AS chunk_id, chunks.text, chunks.chunk_index,
                   documents.id AS document_id, documents.source, documents.title,
                   documents.url, documents.external_id, chunk_embeddings.vector_json
            FROM chunk_embeddings
            JOIN chunks ON chunks.id = chunk_embeddings.chunk_id
            JOIN documents ON documents.id = chunks.document_id
            ORDER BY chunks.id
        """
        params: tuple = tuple()
        if limit:
            sql += " LIMIT ?"
            params = (limit)
        with self.connect() as connection:
            rows = connection.execute(sql, params).fetchall()
        #print(f'{rows=}')
        return [dict(row) for row in rows]

    def lexical_search(self, query: str, limit: int = 30) -> list[dict]:
        self.init_db()
        safe_query = self._fts_query(query)
        if not safe_query:
            return []
        with self.connect() as connection:
            rows = connection.execute(
                """
                SELECT chunks.id AS chunk_id, chunks.text, chunks.chunk_index,
                       documents.id AS document_id, documents.source, documents.title,
                       documents.url, documents.external_id,
                       bm25(chunk_fts) AS lexical_score
                FROM chunk_fts
                JOIN chunks ON chunks.id = chunk_fts.rowid
                JOIN documents ON documents.id = chunks.document_id
                WHERE chunk_fts MATCH ?
                ORDER BY lexical_score
                LIMIT ?
                """,
                (safe_query, limit),
            ).fetchall()
        return [dict(row) for row in rows]

    def rebuild_fts(self) -> int:
        self.init_db()
        with self.connect() as connection:
            try: 
                connection.execute("DELETE FROM chunk_fts")
            except Exception:
                pass
            rows = connection.execute(
                """
                SELECT chunks.id, chunks.text, documents.title, documents.source
                FROM chunks
                JOIN documents ON documents.id = chunks.document_id
                """
            ).fetchall()
            for row in rows:
                connection.execute(
                    "INSERT INTO chunk_fts(rowid, text, title, source) VALUES (?, ?, ?, ?)",
                    (row["id"], row["text"], row["title"], row["source"]),
                )
        return len(rows)

    @staticmethod
    def _fts_query(query: str) -> str:
        terms = []
        for raw in query.replace('"', " ").replace("'", " ").split():
            term = "".join(char for char in raw if char.isalnum() or char in "-_")
            if len(term) >= 2:
                terms.append(term)
        return " OR ".join(terms)

    @staticmethod
    def _hash_text(text: str) -> str:
        return hashlib.sha256(text.encode("utf-8")).hexdigest()