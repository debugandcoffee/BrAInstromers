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
    
    def build_prompt(self, query, results, persona: str = "general"):
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
        
        if persona == "investor":
            task = """FIRST extract and rank relevant entities from the context:
        - companies / startups
        - technologies
        - research groups
        - key people

        FOR EACH ENTITY:
        - provide name
        - provide source-based justification
        - provide link if available in context (URL, paper, dataset, or mention source reference)

        THEN analyze market opportunity:
        1. Market size and growth
        2. Competitive advantage
        3. Monetization potential
        4. Investment attractiveness
        5. Risks
        6. Why top entities matter for this opportunity"""

        elif persona == "company":
            task = """FIRST extract and rank implementation-relevant entities:
        - researchers
        - companies / vendors
        - technologies
        - methods / tools

        FOR EACH ENTITY:
        - explain relevance to the problem
        - include link/source reference if available in context
        - show how it can be contacted or used (if implied by sources)

        THEN analyze:
        1. Technical feasibility
        2. ROI / business value
        3. Integration complexity
        4. Deployment timeline
        5. Recommended collaborators with justification and links"""

        elif persona == "researcher":
            task = """FIRST extract and rank commercialization-relevant entities:
        - companies
        - industries
        - investors
        - applied technologies

        FOR EACH ENTITY:
        - explain why it is relevant
        - include link/source reference if available in context
        - identify real-world connection to research

        THEN translate research into:
        1. Commercial applications
        2. Industry use cases
        3. Potential partners or funders (with links)
        4. Collaboration opportunities
        5. Funding pathways"""

        else:
            task = """FIRST extract all relevant entities:
        - companies
        - researchers
        - investors
        - technologies

        FOR EACH ENTITY:
        - rank relevance
        - justify using context
        - include link/source reference if available

        THEN:
        1. Build entity relationship map
        2. Explain connections between entities
        3. Provide structured answer grounded ONLY in sources"""
        
        return f"""You are analyzing this from a {persona} perspective.

                {task}

                QUERY: {query}

                SOURCES:
                {context}

                Provide structured analysis based ONLY on the context above.""".strip()

    def query(self, user_query: str, persona: str = "general"):
        results = self.retriever.hybrid_with_kg(user_query, top_n=10)
        # results = self.retriever.hybrid(user_query, top_n=8)

        if not results:
            return {
                "answer": "I couldn't find an answer based on the available data.",
                "sources": []
            }

        top_score = max((r.score for r in results), default=0.0)

        # if top_score < 0.25:
        #     return {
        #         "answer": "I couldn't find an answer based on the available data.",
        #         "sources": [r.to_dict() for r in results],
        #         "confidence": float(top_score)
        #     }

        prompt = self.build_prompt(user_query, results, persona=persona)

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

