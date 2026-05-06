from fastapi import APIRouter, HTTPException
from threading import Lock

from app.retrieval.enhanced_search import EnhancedRetriever
from app.storage.document_store import DocumentStore
from app.retrieval.search import Retriever
from app.retrieval.rag_engine import RAGEngine
from app.agents.rag_agent import AgenticRAG
from app.config import settings

router = APIRouter()

_store = None
_retriever = None
_rag_engine = None
_agent = None
_init_lock = Lock()


# def get_agent():
#     global _store, _retriever, _rag_engine, _agent

#     if _agent is not None:
#         return _agent

#     with _init_lock:
#         if _agent is not None:
#             return _agent

#         try:
#             _store = DocumentStore(settings.document_db_path)
#             _retriever = Retriever(_store)
#             _rag_engine = RAGEngine(_retriever)
#             _agent = AgenticRAG(_rag_engine)

#         except Exception as e:
#             raise RuntimeError(f"RAG system initialization failed: {e}")

#     return _agent


def get_rag():
    global _store, _retriever, _rag_engine


    with _init_lock:
        try:
            _store = DocumentStore(settings.document_db_path)
            _retriever = EnhancedRetriever(_store, use_kg=True)
            _rag_engine = RAGEngine(_retriever)

        except Exception as e:
            raise RuntimeError(f"RAG system initialization failed: {e}")

    return _rag_engine


@router.get("/search")
def search(q: str):
    if not q or not q.strip():
        raise HTTPException(
            status_code=400,
            detail="Query cannot be empty"
        )

    rag = get_rag()

    try:
        result = rag.query(q)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"RAG processing failed: {str(e)}"
        )

    return {
        "query": q,
        "result": result
    }


@router.get("/health")
def health():
    return {"status": "ok"}
