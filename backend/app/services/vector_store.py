import json
import os
import shutil
from pathlib import Path
from typing import Dict, List, Optional
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document

from app.config import settings
from app.models.schemas import DocumentInfo
from app.services.embeddings import get_embedding_model

_vector_store_instance: Optional[FAISS] = None


def _get_catalog_file() -> Path:
    data_dir = Path(settings.data_dir)
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir / "documents.json"


def load_documents_catalog() -> Dict[str, dict]:
    catalog_path = _get_catalog_file()
    if not catalog_path.exists():
        return {}
    try:
        with open(catalog_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def save_documents_catalog(catalog: Dict[str, dict]) -> None:
    catalog_path = _get_catalog_file()
    with open(catalog_path, "w", encoding="utf-8") as f:
        json.dump(catalog, f, indent=2)


def get_all_documents_metadata() -> List[DocumentInfo]:
    catalog = load_documents_catalog()
    return [DocumentInfo(**info) for info in catalog.values()]


def get_document_metadata(document_id: str) -> Optional[DocumentInfo]:
    catalog = load_documents_catalog()
    info = catalog.get(document_id)
    if info:
        return DocumentInfo(**info)
    return None


def save_document_metadata(doc_info: DocumentInfo) -> None:
    catalog = load_documents_catalog()
    catalog[doc_info.id] = doc_info.model_dump()
    save_documents_catalog(catalog)


def delete_document_metadata(document_id: str) -> Optional[DocumentInfo]:
    catalog = load_documents_catalog()
    if document_id in catalog:
        deleted = catalog.pop(document_id)
        save_documents_catalog(catalog)
        return DocumentInfo(**deleted)
    return None


def get_vector_store() -> Optional[FAISS]:
    global _vector_store_instance
    if _vector_store_instance is not None:
        return _vector_store_instance

    store_path = Path(settings.vector_store_path)
    index_file = store_path / "index.faiss"
    if store_path.exists() and index_file.exists():
        embeddings = get_embedding_model()
        _vector_store_instance = FAISS.load_local(
            str(store_path),
            embeddings,
            allow_dangerous_deserialization=True
        )
        return _vector_store_instance

    return None


def add_documents_to_store(documents: List[Document]) -> None:
    global _vector_store_instance
    if not documents:
        return

    embeddings = get_embedding_model()
    store = get_vector_store()

    if store is None:
        store = FAISS.from_documents(documents, embeddings)
        _vector_store_instance = store
    else:
        store.add_documents(documents)

    store_path = Path(settings.vector_store_path)
    store_path.mkdir(parents=True, exist_ok=True)
    store.save_local(str(store_path))


def delete_document_vectors(document_id: str) -> bool:
    global _vector_store_instance
    store = get_vector_store()
    if store is None:
        return False

    # Find all keys matching document_id in FAISS docstore
    keys_to_delete = [
        k for k, doc in store.docstore._dict.items()
        if doc.metadata.get("document_id") == document_id
    ]

    if not keys_to_delete:
        return False

    store.delete(keys_to_delete)

    # Persist the updated index or clear if empty
    store_path = Path(settings.vector_store_path)
    if len(store.docstore._dict) == 0:
        if store_path.exists():
            shutil.rmtree(str(store_path))
        _vector_store_instance = None
    else:
        store.save_local(str(store_path))

    return True


def clear_all_data() -> None:
    global _vector_store_instance
    _vector_store_instance = None
    store_path = Path(settings.vector_store_path)
    if store_path.exists():
        shutil.rmtree(str(store_path))
    catalog_path = _get_catalog_file()
    if catalog_path.exists():
        catalog_path.unlink()
