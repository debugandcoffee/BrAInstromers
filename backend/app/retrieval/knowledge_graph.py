from __future__ import annotations

from dataclasses import dataclass
from typing import Optional
import json


@dataclass
class QueryAnalysis:
    intent: str
    keywords: list[str]
    entities: list[str]
    temporal_context: str
    strategy: str


class KnowledgeGraph:
    
    DEFAULT_KEYWORDS = {
        "technology": ["ai", "machine learning", "software", "hardware"],
        "business": ["market", "company", "startup", "strategy"],
        "science": ["research", "study", "experiment", "data"],
        "general": ["system", "process", "model", "analysis"],
    }
    
    SOURCE_AUTHORITY = {
        "academic": 0.9,
        "official": 0.85,
        "database": 0.75,
        "web": 0.6,
    }
    
    def __init__(self, keyword_config: Optional[dict] = None):
        self.entity_graph: dict[str, set[str]] = {}
        self.keywords_config = keyword_config or self.DEFAULT_KEYWORDS
    
    def analyze_query(self, query: str) -> QueryAnalysis:
        query_lower = query.lower()
        
        intent = self._detect_intent(query_lower)
        keywords = self._extract_keywords(query_lower)
        entities = self._extract_entities(query_lower)
        temporal_context = self._detect_temporal_context(query_lower)
        strategy = self._recommend_strategy(intent, keywords, query_lower)
        
        return QueryAnalysis(
            intent=intent,
            keywords=keywords,
            entities=entities,
            temporal_context=temporal_context,
            strategy=strategy,
        )
    
    def get_source_weight(self, source: str) -> float:
        return self.SOURCE_AUTHORITY.get(source, 0.5)
    
    def should_boost_result(self, query_entities: list[str], result_text: str) -> float:
        if not query_entities:
            return 1.0
        
        text_lower = result_text.lower()
        mentions = sum(1 for e in query_entities if e in text_lower)
        
        if mentions == 0:
            return 1.0
        
        return 1.0 + min(mentions * 0.10, 0.25)
    
    def extract_keywords_from_text(self, text: str) -> dict[str, float]:
        text_lower = text.lower()
        scores = {}
        
        for category, keywords in self.keywords_config.items():
            for keyword in keywords:
                count = text_lower.count(keyword)
                if count > 0:
                    scores[keyword] = min(count / 5.0, 1.0)
        
        return scores
    
    @staticmethod
    def _detect_intent(query: str) -> str:
        if any(w in query for w in ["which", "what", "who", "where", "when"]):
            return "factual"
        if any(w in query for w in ["compare", "vs", "difference", "versus"]):
            return "comparative"
        if any(w in query for w in ["how many", "how much", "count", "statistics", "data"]):
            return "numerical"
        if any(w in query for w in ["future", "predict", "forecast"]):
            return "prospective"
        if any(w in query for w in ["explain", "learn", "research", "study"]):
            return "research"
        return "factual"
    
    @staticmethod
    def _extract_keywords(query: str) -> list[str]:
        stopwords = {
            "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for",
            "of", "is", "are", "was", "were", "be", "been", "being",
            "have", "has", "had", "do", "does", "did",
            "will", "would", "could", "should", "may", "might", "can",
            "this", "that", "these", "those",
            "i", "you", "he", "she", "it", "we", "they",
            "what", "which", "who", "where", "when", "why", "how"
        }
        return [w for w in query.split() if len(w) > 3 and w not in stopwords]
    
    @staticmethod
    def _extract_entities(query: str) -> list[str]:
        known_entities = {
            "openai", "google", "microsoft", "amazon",
            "python", "tensorflow", "pytorch",
            "machine learning", "artificial intelligence"
        }
        return [e for e in known_entities if e in query]
    
    @staticmethod
    def _detect_temporal_context(query: str) -> str:
        if any(w in query for w in ["recent", "latest", "new", "2024", "2025", "2026"]):
            return "recent"
        if any(w in query for w in ["future", "predict", "forecast"]):
            return "future"
        if any(w in query for w in ["historical", "past", "before"]):
            return "historical"
        return "any"
    
    @staticmethod
    def _recommend_strategy(intent: str, keywords: list[str], query: str) -> str:
        if len(keywords) <= 2 and len(query) < 40:
            return "lexical"
        if len(keywords) > 5 or len(query) > 80:
            return "semantic"
        return "hybrid"