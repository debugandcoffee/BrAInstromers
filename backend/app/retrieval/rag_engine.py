from openai import OpenAI
from app.retrieval.search import Retriever
from app.config import settings
from app.storage.document_store import DocumentStore
from app.retrieval.enhanced_search import EnhancedRetriever

client = OpenAI(
    api_key=settings.openai_api_key,
    base_url="https://api.groq.com/openai/v1"
)


class RAGEngine:
    def __init__(self, retriever: Retriever):
        self.retriever = retriever

    def _get_system_prompt(self, persona: str = "general") -> str:
        base = "You are a strict RAG system. Never hallucinate. Use ONLY the provided context."
        
        if persona == "investor":
            return base + "\n\nYou are an investor analyst. Assess market size, competition, defensibility, traction signals, funding fit, risk, grant leverage, and next diligence questions. Prefer structured recommendations and clear assumptions."
        elif persona == "researcher":
            return base + "\n\nYou are a research commercialization analyst. Help identify industry use cases, business buyers, grant programs, pilot partners, and go-to-market hypotheses. Be specific, evidence-oriented, and ask for missing technical constraints when needed."
        elif persona == "company":
            return base + "\n\nYou are a business development strategist. Help companies find technologies, startups, researchers, vendors, grants, and partnerships that solve operational or growth problems. Focus on practical adoption paths and buyer language."
        
        return base

    # def build_prompt(self, query, results):
    #     context = "\n\n".join(
    #         f"{r.title}\n{r.text[:400]}" for r in results
    #     )

    #     return f"""
    #         You are a STRICT retrieval-based AI assistant.

    #         RULES:
    #         - Use ONLY the provided context.
    #         - If the context does not contain the answer, say:
    #         "I couldn't find an answer based on the available data."
    #         - Do NOT use external knowledge.
    #         - Do NOT guess or hallucinate.
    #         - If context is weak or irrelevant, refuse.

    #         TASK:
    #         Answer the user query using only the context.

    #         USER QUERY:
    #         {query}

    #         CONTEXT:
    #         {context}

    #         OUTPUT FORMAT:
    #         - concise answer
    #         - list of relevant entities (investors / companies / researchers)
    #         - short justification based ONLY on context
    #         """.strip()
    
    def build_prompt(self, query, results):
        by_source = {}
        for r in results:
            if r.source not in by_source:
                by_source[r.source] = []
            by_source[r.source].append(r)
        
        diverse_results = []
        for source in sorted(by_source.keys())[:5]:
            diverse_results.append(by_source[source][0])
        
        context = "\n\n".join(
            f"[{r.source}] {r.title}\n{r.text[:400]}" for r in diverse_results
        )
        
        return f"""You are a business matchmaker connecting research with companies.
        
            ANALYZE the query and results to identify:
            1. If this is a company problem, researcher, or research idea
            2. Which entities (researchers/companies/investors) match best
            3. HOW each match solves the problem (business value translation)

            QUERY: {query}

            RESULTS:
            {context}

            OUTPUT JSON:
            {{
                "entity_type": "company_problem|researcher_profile|research_idea",
                "extracted": {{"description": "...", "key_needs": [...]}},
                "matches": [
                    {{
                        "name": "...",
                        "type": "researcher|company|investor",
                        "score": 0.85,
                        "why": "How they solve this in business terms",
                        "next_step": "Specific action"
                    }}
                ]
            }}"""

    def query(self, user_query: str, persona: str = "general"):
        results = self.retriever.hybrid_with_kg(user_query, top_n=8)
        # results = self.retriever.hybrid(user_query, top_n=8)

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

        prompt = self.build_prompt(user_type, user_query, results)

        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {
                    "role": "system",
                    "content": self._get_system_prompt(persona)
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

