from openai import OpenAI
from app.retrieval.search import Retriever

client = OpenAI()


class RAGEngine:
    def __init__(self, retriever: Retriever):
        self.retriever = retriever

    def build_prompt(self, query, results):
        context = "\n\n".join(
            f"{r.title}\n{r.text[:400]}" for r in results
        )

        return f"""
            You are a STRICT retrieval-based AI assistant.

            RULES:
            - Use ONLY the provided context.
            - If the context does not contain the answer, say:
            "I couldn't find an answer based on the available data."
            - Do NOT use external knowledge.
            - Do NOT guess or hallucinate.
            - If context is weak or irrelevant, refuse.

            TASK:
            Answer the user query using only the context.

            USER QUERY:
            {query}

            CONTEXT:
            {context}

            OUTPUT FORMAT:
            - concise answer
            - list of relevant entities (investors / companies / researchers)
            - short justification based ONLY on context
            """.strip()

    def query(self, user_query: str):
        results = self.retriever.hybrid(user_query, top_n=8)

        if not results:
            return {
                "answer": "I couldn't find an answer based on the available data.",
                "sources": []
            }

        top_score = max((r.score for r in results), default=0.0)

        if top_score < 0.25:
            return {
                "answer": "I couldn't find an answer based on the available data.",
                "sources": [r.to_dict() for r in results],
                "confidence": float(top_score)
            }

        prompt = self.build_prompt(user_query, results)

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": "You are a strict RAG system. Never hallucinate."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.1
        )

        answer = response.choices[0].message.content

        return {
            "answer": answer,
            "sources": [r.to_dict() for r in results],
            "confidence": float(top_score)
        }

