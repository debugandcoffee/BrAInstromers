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
            You are an AI research assistant.

            User query:
            {query}

            Context:
            {context}

            Return:
            - relevant investors / companies / researchers
            - explanation why relevant
            - structured and concise answer
            """

    def query(self, user_query: str):
        results = self.retriever.hybrid(user_query, top_n=8)

        prompt = self.build_prompt(user_query, results)

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
        )

        return {
            "answer": response.choices[0].message.content,
            "sources": [r.to_dict() for r in results],
        }
