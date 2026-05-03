from app.agents.query_agent import QueryImproverAgent


class AgenticRAG:
    def __init__(self, rag_engine):
        self.rag = rag_engine
        self.agent = QueryImproverAgent()

    def query(self, user_query: str, expected: str | None = None):
        result = self.rag.query(user_query)

        answer = result["answer"]
        score = 0.0

        if expected:
            score = self._simple_score(expected, answer)

        if score < 0.6:
            improved_query = self.agent.improve(user_query, score)
            result = self.rag.query(improved_query)

            return {
                "answer": result["answer"],
                "final_query": improved_query,
                "score": score,
                "sources": result["sources"]
            }

        return {
            "answer": answer,
            "final_query": user_query,
            "score": score,
            "sources": result["sources"]
        }

    def _simple_score(self, expected: str, actual: str) -> float:
        e = set(expected.lower().split())
        a = set(actual.lower().split())

        if not e:
            return 0.0

        return len(e & a) / len(e)
    