from __future__ import annotations

from app.retrieval.search import Retriever, SearchResult
from app.retrieval.knowledge_graph import KnowledgeGraph
from app.config import settings
from app.storage.document_store import DocumentStore


class EnhancedRetriever(Retriever):
    """
    Retriever with optional knowledge-graph-aware ranking.
    Fully backward compatible with base Retriever.
    """

    def __init__(
        self,
        store: DocumentStore,
        model_name: str = settings.embedding_model,
        use_kg: bool = True,
    ):
        super().__init__(store, model_name)
        self.kg = KnowledgeGraph() if use_kg else None

    def hybrid_with_kg(
        self,
        query: str,
        top_n: int = 10,
        candidate_n: int = 80,
        semantic_weight: float = 0.65,
        lexical_weight: float = 0.35,
        enable_diversity: bool = True,
    ) -> list[SearchResult]:
        if not self.kg:
            return self.hybrid(query, top_n, candidate_n, semantic_weight, lexical_weight)

        results = self.hybrid(query, top_n, candidate_n, semantic_weight, lexical_weight)
        analysis = self.kg.analyze_query(query)

        results = self._apply_kg_ranking(results, analysis)

        return self._diversify(results, top_n) if enable_diversity else results[:top_n]

    def semantic_with_kg(
        self,
        query: str,
        top_n: int = 10,
        enable_diversity: bool = True,
    ) -> list[SearchResult]:
        if not self.kg:
            return self.semantic(query, top_n)

        results = self.semantic(query, top_n * 3)
        analysis = self.kg.analyze_query(query)

        enhanced = []
        for r in results:
            score = r.score

            score *= self.kg.should_boost_result(analysis.entities, r.text)
            score *= self.kg.get_source_weight(r.source)

            enhanced.append(
                SearchResult(
                    **{**r.__dict__, "score": score}
                )
            )

        enhanced.sort(key=lambda x: x.score, reverse=True)
        return self._diversify(enhanced, top_n) if enable_diversity else enhanced[:top_n]

    def _apply_kg_ranking(
        self,
        results: list[SearchResult],
        analysis,
    ) -> list[SearchResult]:
        enriched = []

        for r in results:
            score = r.score

            score *= self.kg.should_boost_result(analysis.entities, r.text)
            score *= self.kg.get_source_weight(r.source)

            keyword_hits = self.kg.extract_keywords_from_text(r.text)
            if keyword_hits:
                score *= (1.0 + min(len(keyword_hits) * 0.01, 0.15))

            enriched.append(
                SearchResult(
                    **{**r.__dict__, "score": score}
                )
            )

        enriched.sort(key=lambda x: x.score, reverse=True)
        return enriched

    @staticmethod
    def _diversify(results: list[SearchResult], top_n: int) -> list[SearchResult]:
        seen_sources = set()
        diversified = []

        for r in results:
            if len(diversified) >= top_n:
                break
            if r.source not in seen_sources:
                diversified.append(r)
                seen_sources.add(r.source)

        for r in results:
            if len(diversified) >= top_n:
                break
            if r not in diversified:
                diversified.append(r)

        return diversified