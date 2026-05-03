from fastapi import APIRouter, HTTPException

from app.storage.document_store import DocumentStore
from app.retrieval.search import Retriever
from app.retrieval.rag_engine import RAGEngine
from app.config import settings

router = APIRouter()

_store = None
_retriever = None
_rag = None


def get_rag():
    global _store, _retriever, _rag

    if _rag is None:
        try:
            _store = DocumentStore(settings.document_db_path)
            _retriever = Retriever(_store)
            _rag = RAGEngine(_retriever)
        except Exception as e:
            raise RuntimeError(f"RAG init failed: {e}")

    return _rag


@router.get("/search")
def search(q: str):
    if not q:
        raise HTTPException(status_code=400, detail="Query cannot be empty")

    rag = get_rag()
    return rag.query(q)


@router.get("/health")
def health():
    return {"status": "ok"}
