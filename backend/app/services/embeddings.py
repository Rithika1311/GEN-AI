import os
from langchain_community.embeddings import HuggingFaceEmbeddings
from app.config import settings

_embedding_instance = None


def get_embedding_model() -> HuggingFaceEmbeddings:
    # Cache the local sentence-transformers model to avoid reloading weights per request
    global _embedding_instance
    if _embedding_instance is None:
        model_kwargs = {"device": "cpu"}
        encode_kwargs = {"normalize_embeddings": True}
        try:
            # Try offline first if weights are already cached locally
            _embedding_instance = HuggingFaceEmbeddings(
                model_name=settings.embedding_model_name,
                model_kwargs={**model_kwargs, "local_files_only": True},
                encode_kwargs=encode_kwargs,
            )
        except Exception:
            # Fallback to standard loading if not cached yet
            _embedding_instance = HuggingFaceEmbeddings(
                model_name=settings.embedding_model_name,
                model_kwargs=model_kwargs,
                encode_kwargs=encode_kwargs,
            )
    return _embedding_instance
