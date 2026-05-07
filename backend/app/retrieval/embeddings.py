from __future__ import annotations

import os

from app.config import settings


class EmbeddingModel:
    def __init__(self, model_name: str = settings.embedding_model):
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError as exc:
            raise RuntimeError("Install retrieval dependencies first: pip install -r requirements.txt") from exc

        self.model_name = model_name
        local_only = os.getenv("HF_HUB_OFFLINE") == "1" or os.getenv("TRANSFORMERS_OFFLINE") == "1"
        self.model = SentenceTransformer(model_name, local_files_only=local_only)

    def encode_passages(self, texts: list[str]) -> list[list[float]]:
        prefixed = [f"passage: {text}" for text in texts]
        return self.model.encode(prefixed, normalize_embeddings=True).tolist()

    def encode_query(self, query: str) -> list[float]:
        return self.model.encode([f"query: {query}"], normalize_embeddings=True)[0].tolist()


class RerankerModel:
    def __init__(self, model_name: str = settings.reranker_model):
        try:
            from sentence_transformers import CrossEncoder
        except ImportError as exc:
            raise RuntimeError("Install retrieval dependencies first: pip install -r requirements.txt") from exc

        self.model = CrossEncoder(model_name)

    def rerank(self, query: str, passages: list[str]) -> list[float]:
        pairs = [[query, passage] for passage in passages]
        scores = self.model.predict(pairs)
        return scores.tolist()
