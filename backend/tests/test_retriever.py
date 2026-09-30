from langchain_core.documents import Document
from app.services.retriever import retrieve_context, calculate_cosine_similarity
from app.services.vector_store import add_documents_to_store, clear_all_data


def test_cosine_similarity_calculation():
    # Exactly identical vectors have L2 distance 0.0 -> similarity 1.0
    assert calculate_cosine_similarity(0.0) == 1.0
    # Orthogonal vectors have L2 distance sqrt(2) ~ 1.414 -> similarity 0.0
    assert abs(calculate_cosine_similarity(1.41421356)) < 0.01


def test_similarity_threshold_filtering(tmp_path, monkeypatch):
    test_dir = str(tmp_path / "test_data")
    monkeypatch.setattr("app.config.settings.data_dir", test_dir)
    monkeypatch.setattr("app.config.settings.vector_store_path", str(tmp_path / "test_data" / "faiss"))
    monkeypatch.setattr("app.config.settings.similarity_threshold", 0.35)
    clear_all_data()

    docs = [
        Document(
            page_content="Python was created by Guido van Rossum in the late 1980s.",
            metadata={"document_id": "doc-py", "filename": "python.pdf", "page": 1, "chunk_index": 0}
        )
    ]
    add_documents_to_store(docs)

    # In-scope question: should find the document
    relevant_hits = retrieve_context("Who created the Python language?")
    assert len(relevant_hits) > 0
    assert relevant_hits[0].filename == "python.pdf"
    assert relevant_hits[0].page == 1

    # Out-of-scope question: should be rejected by threshold and return empty
    irrelevant_hits = retrieve_context("What is the recipe for making sourdough bread?")
    assert len(irrelevant_hits) == 0

    clear_all_data()


def test_document_id_filtering(tmp_path, monkeypatch):
    test_dir = str(tmp_path / "test_data")
    monkeypatch.setattr("app.config.settings.data_dir", test_dir)
    monkeypatch.setattr("app.config.settings.vector_store_path", str(tmp_path / "test_data" / "faiss"))
    monkeypatch.setattr("app.config.settings.similarity_threshold", 0.1)
    clear_all_data()

    docs = [
        Document(
            page_content="Database indexing speeds up SQL queries significantly.",
            metadata={"document_id": "doc-db", "filename": "database.pdf", "page": 2, "chunk_index": 0}
        ),
        Document(
            page_content="Operating system scheduling algorithms include round robin and priority.",
            metadata={"document_id": "doc-os", "filename": "os.pdf", "page": 1, "chunk_index": 0}
        )
    ]
    add_documents_to_store(docs)

    # Filter strictly for doc-os
    os_hits = retrieve_context("scheduling algorithms", document_ids=["doc-os"])
    assert len(os_hits) > 0
    assert all(h.document_id == "doc-os" for h in os_hits)

    clear_all_data()
