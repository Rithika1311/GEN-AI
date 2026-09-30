from typing import List, Optional
from app.config import settings
from app.models.schemas import SourceCitation
from app.services.vector_store import get_vector_store


def calculate_cosine_similarity(l2_distance: float) -> float:
    # Normalized embeddings relate L2 distance to cosine similarity via: S = 1 - (d^2)/2
    cos_sim = 1.0 - (l2_distance ** 2) / 2.0
    return max(0.0, min(1.0, cos_sim))


def retrieve_context(
    query: str,
    document_ids: Optional[List[str]] = None,
    top_k: int = settings.top_k,
    threshold: float = settings.similarity_threshold,
) -> List[SourceCitation]:
    store = get_vector_store()
    if store is None or len(store.docstore._dict) == 0:
        return []

    # Build metadata filter if specific documents are selected
    filter_fn = None
    if document_ids:
        doc_id_set = set(document_ids)
        filter_fn = lambda m: m.get("document_id") in doc_id_set

    # 1. Similarity search with score to evaluate relevance threshold
    try:
        score_candidates = store.similarity_search_with_score(
            query,
            k=top_k,
            filter=filter_fn
        )
    except Exception:
        # If filter matches zero documents in FAISS, it may raise or return empty
        return []

    if not score_candidates:
        return []

    # Map doc content to its cosine similarity score
    score_map = {}
    for doc, l2_dist in score_candidates:
        score_map[doc.page_content] = calculate_cosine_similarity(l2_dist)

    best_similarity = score_map.get(score_candidates[0][0].page_content, 0.0)

    # If top retrieved passage falls below similarity threshold, reject as out-of-scope
    if best_similarity < threshold:
        return []

    # 2. MMR (Maximal Marginal Relevance) to select diverse, non-redundant passages
    try:
        mmr_docs = store.max_marginal_relevance_search(
            query,
            k=top_k,
            fetch_k=min(top_k * 3, len(store.docstore._dict)),
            filter=filter_fn
        )
    except Exception:
        # Fallback to similarity search candidates if MMR encounters indexing constraints
        mmr_docs = [doc for doc, _ in score_candidates]

    citations: List[SourceCitation] = []
    for doc in mmr_docs:
        meta = doc.metadata
        sim_score = score_map.get(doc.page_content, best_similarity)
        citations.append(
            SourceCitation(
                document_id=meta.get("document_id", "unknown"),
                filename=meta.get("filename", "unknown.pdf"),
                page=meta.get("page", 1),
                chunk_index=meta.get("chunk_index", 0),
                text=doc.page_content,
                similarity_score=round(sim_score, 4),
            )
        )

    return citations
