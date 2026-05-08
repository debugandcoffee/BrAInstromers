from __future__ import annotations

import json
import math
from dataclasses import dataclass
from typing import Any

from app.config import settings
from app.retrieval.embeddings import EmbeddingModel, RerankerModel
from app.storage.document_store import DocumentStore


@dataclass(frozen=True)
class SearchResult:
    chunk_id: int
    document_id: int
    source: str
    title: str
    url: str | None
    external_id: str
    chunk_index: int
    text: str
    score: float
    semantic_score: float = 0.0
    lexical_score: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "chunk_id": self.chunk_id,
            "document_id": self.document_id,
            "source": self.source,
            "title": self.title,
            "url": self.url,
            "external_id": self.external_id,
            "chunk_index": self.chunk_index,
            "score": round(self.score, 6),
            "semantic_score": round(self.semantic_score, 6),
            "lexical_score": round(self.lexical_score, 6),
            "preview": self.text[:900],
        }


class Retriever:
    def __init__(self, store: DocumentStore, model_name: str = settings.embedding_model):
        self.store = store
        self.model_name = model_name
        self.reranker = RerankerModel()

    def lexical(self, query: str, top_n: int = 10, candidate_n: int = 50) -> list[SearchResult]:
        rows = self.store.lexical_search(query, limit=max(top_n, candidate_n))
        normalized = self._normalize_lexical(rows)
        return [
            self._row_to_result(
                row,
                score=normalized.get(int(row["chunk_id"]), 0.0),
                lexical_score=normalized.get(int(row["chunk_id"]), 0.0),
            )
            for row in rows[:top_n]
        ]

    def semantic(self, query: str, top_n: int = 10) -> list[SearchResult]:
        embedder = EmbeddingModel(self.model_name)
        query_vector = embedder.encode_query(query)
        scored = []
        for row in self.store.semantic_candidates(self.model_name):
            score = cosine_similarity(query_vector, json.loads(row["vector_json"]))
            scored.append((score, row))
        scored.sort(key=lambda item: item[0], reverse=True)
        return [
            self._row_to_result(row, score=score, semantic_score=score)
            for score, row in scored[:top_n]
        ]

    def hybrid(
        self,
        query: str,
        top_n: int = 10,
        candidate_n: int = 80,
        semantic_weight: float = 0.65,
        lexical_weight: float = 0.35,
    ) -> list[SearchResult]:
        embedder = EmbeddingModel(self.model_name)
        query_vector = embedder.encode_query(query)

        semantic_scores: dict[int, float] = {}
        row_by_id: dict[int, dict] = {}
        for row in self.store.semantic_candidates(self.model_name):
            chunk_id = int(row["chunk_id"])
            row_by_id[chunk_id] = row
            semantic_scores[chunk_id] = cosine_similarity(query_vector, json.loads(row["vector_json"]))

        top_semantic_ids = sorted(semantic_scores, key=semantic_scores.get, reverse=True)[:candidate_n]
        lexical_rows = self.store.lexical_search(query, limit=candidate_n)
        lexical_scores = self._normalize_lexical(lexical_rows)
        for row in lexical_rows:
            row_by_id[int(row["chunk_id"])] = row

        semantic_norm = normalize_scores({chunk_id: semantic_scores[chunk_id] for chunk_id in top_semantic_ids})
        candidate_ids = set(top_semantic_ids) | set(lexical_scores)

        #print(f'{self.store.semantic_candidates(self.model_name)=}')
        #print(f'{self.model_name=}')
        #print(f'{lexical_rows=}')
        #print(f'{semantic_scores=}')
        #print(f'{semantic_norm=}')

        #print(top_semantic_ids)
        #print(lexical_scores)
        #print(candidate_ids)

        results: list[SearchResult] = []
        for chunk_id in candidate_ids:
            row = row_by_id[chunk_id]
            semantic_score = semantic_norm.get(chunk_id, 0.0)
            lexical_score = lexical_scores.get(chunk_id, 0.0)
            score = semantic_weight * semantic_score + lexical_weight * lexical_score
            results.append(
                self._row_to_result(
                    row,
                    score=score,
                    semantic_score=semantic_score,
                    lexical_score=lexical_score,
                )
            )
        #print("Res1:")
        #print(results)

        # Rerank top candidates
        if len(results) > top_n:
            rerank_candidates = sorted(results, key=lambda r: r.score, reverse=True)[:20]  # Top 20 for reranking
            passages = [r.text for r in rerank_candidates]
            rerank_scores = self.reranker.rerank(query, passages)
            # Create new SearchResult with reranked scores
            reranked_results = []
            for i, r in enumerate(rerank_candidates):
                reranked_results.append(SearchResult(
                    chunk_id=r.chunk_id,
                    document_id=r.document_id,
                    source=r.source,
                    title=r.title,
                    url=r.url,
                    external_id=r.external_id,
                    chunk_index=r.chunk_index,
                    text=r.text,
                    score=rerank_scores[i],
                    semantic_score=r.semantic_score,
                    lexical_score=r.lexical_score,
                ))
            # Replace top candidates with reranked ones
            results = reranked_results + [r for r in results if r not in rerank_candidates]

        #print("Res2:")
        #print(results)

        results.sort(key=lambda result: result.score, reverse=True)
        return results[:top_n]

    @staticmethod
    def _normalize_lexical(rows: list[dict]) -> dict[int, float]:
        if not rows:
            return {}
        raw = {int(row["chunk_id"]): -float(row["lexical_score"]) for row in rows}
        return normalize_scores(raw)

    @staticmethod
    def _row_to_result(
        row: dict,
        score: float,
        semantic_score: float = 0.0,
        lexical_score: float = 0.0,
    ) -> SearchResult:
        return SearchResult(
            chunk_id=int(row["chunk_id"]),
            document_id=int(row["document_id"]),
            source=str(row["source"]),
            title=str(row["title"]),
            url=row["url"],
            external_id=str(row["external_id"]),
            chunk_index=int(row["chunk_index"]),
            text=str(row["text"]),
            score=score,
            semantic_score=semantic_score,
            lexical_score=lexical_score,
        )


def cosine_similarity(left: list[float], right: list[float]) -> float:
    dot = sum(a * b for a, b in zip(left, right))
    left_norm = math.sqrt(sum(a * a for a in left))
    right_norm = math.sqrt(sum(b * b for b in right))
    if left_norm == 0 or right_norm == 0:
        return 0.0
    return dot / (left_norm * right_norm)


def normalize_scores(scores: dict[int, float]) -> dict[int, float]:
    if not scores:
        return {}
    values = list(scores.values())
    min_score = min(values)
    max_score = max(values)
    if max_score == min_score:
        return {key: 1.0 for key in scores}
    return {key: (value - min_score) / (max_score - min_score) for key, value in scores.items()}
