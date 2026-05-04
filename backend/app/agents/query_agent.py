from sklearn.feature_extraction.text import ENGLISH_STOP_WORDS

STOPWORDS = set(ENGLISH_STOP_WORDS)


class QueryImproverAgent:
    def improve(self, query: str, score: float) -> str:
        if score >= 0.6:
            return query

        return self._expand(query, score)

    def _expand(self, query: str, score: float) -> str:
        keywords = self._extract_keywords(query)

        if score < 0.3:
            booster = "relevant information background overview key entities details"
        else:
            booster = "related concepts context"

        return f"{query} {' '.join(keywords)} {booster}"

    def _extract_keywords(self, query: str) -> list[str]:
        tokens = query.lower().replace("?", "").split()

        return [
            t for t in tokens
            if t not in STOPWORDS and len(t) > 2
        ]
