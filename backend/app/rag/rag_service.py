from ..core.config import settings
from .bm25_store import bm25_store, simple_tokenize
from .embeddings import get_embedding_service
from .vector_store import vector_store
from langsmith import traceable


def _meta_key(meta: dict) -> str:
    question = meta.get("question", "")
    answer = meta.get("answer", "")
    return f"{question}|||{answer}"


def _rrf_fuse(result_lists: list[list[dict]], k: int) -> list[dict]:
    fused: dict[str, dict] = {}
    for results in result_lists:
        for rank, res in enumerate(results, start=1):
            meta = res.get("metadata", {})
            key = _meta_key(meta)
            entry = fused.get(key)
            if entry is None:
                entry = {"metadata": meta, "score": 0.0}
                fused[key] = entry
            entry["score"] += 1.0 / (k + rank)

    return sorted(fused.values(), key=lambda item: item["score"], reverse=True)

class RAGService:
    def __init__(self):
        self.embedding_service = get_embedding_service()
        self.vector_store = vector_store
        self.bm25_store = bm25_store

    def retrieve_dense(self, query: str, k: int = 3) -> list[dict]:
        query_embedding = self.embedding_service.encode([query])[0]
        return self.vector_store.search(query_embedding, k=k)

    def retrieve_bm25(self, query: str, k: int = 3) -> list[dict]:
        query_tokens = simple_tokenize(query)
        if not query_tokens:
            return []
        return self.bm25_store.search(query_tokens, k=k)

    def retrieve_hybrid(self, query: str, k: int = 3) -> list[dict]:
        dense_k = settings.HYBRID_DENSE_K
        bm25_k = settings.HYBRID_BM25_K
        rrf_k = settings.HYBRID_RRF_K

        dense_results = self.retrieve_dense(query, k=dense_k)
        bm25_results = self.retrieve_bm25(query, k=bm25_k)

        fused = _rrf_fuse([dense_results, bm25_results], rrf_k)
        return fused[:k]

    @traceable(name="RAG Retrieval")
    def retrieve(self, query: str, k: int = 3, mode: str = "hybrid") -> list[dict]:
        """Retrieve relevant documents using the chosen strategy."""
        if mode == "bm25":
            return self.retrieve_bm25(query, k=k)
        if mode == "dense":
            return self.retrieve_dense(query, k=k)
        return self.retrieve_hybrid(query, k=k)

    def format_context(self, results: list[dict]) -> str:
        """
        Formats retrieved documents into a context string for the LLM.
        """
        context_parts = []
        for i, res in enumerate(results):
            meta = res['metadata']
            question = meta.get('question', '')[:100]  # Truncate question
            answer = meta.get('answer', '')[:200]  # Truncate answer
            context_parts.append(f"Source {i+1} (Type: {meta.get('qtype', 'general')}):\nQ: {question}\nA: {answer}")
        
        return "\n\n".join(context_parts)

rag_service = RAGService()
