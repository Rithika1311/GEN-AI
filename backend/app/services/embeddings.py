from langchain_community.embeddings import HuggingFaceEmbeddings
from app.config import settings

_embedding_instance = None


def get_embedding_model() -> HuggingFaceEmbeddings:
    # Cache the local sentence-transformers model to avoid reloading weights per request
    global _embedding_instance
    if _embedding_instance is None:
        _embedding_instance = HuggingFaceEmbeddings(
            model_name=settings.embedding_model_name,
            model_kwargs={"device": "cpu"},
            encode_kwargs={"normalize_embeddings": True}  # Normalizes vectors for cosine similarity
        )
    return _embedding_instance
