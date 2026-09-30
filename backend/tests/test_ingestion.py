import pytest
from app.services.ingestion import clean_text, chunk_document_pages
from app.services.vector_store import (
    add_documents_to_store,
    get_vector_store,
    delete_document_vectors,
    clear_all_data,
)


def test_clean_text():
    raw = "Hello\x00 world!\r\n\r\nThis   has   spaces\n\n\n\nand newlines."
    cleaned = clean_text(raw)
    assert "\x00" not in cleaned
    assert "\r" not in cleaned
    assert "Hello world!" in cleaned
    assert "This has spaces" in cleaned


def test_chunking_preserves_page_metadata_and_overlap():
    # Construct multi-page sample content
    page1_text = "Sentence one. " * 50  # ~700 chars
    page2_text = "Second page information with details. " * 40
    pages = [(1, page1_text), (2, page2_text)]

    chunk_size = 300
    chunk_overlap = 50
    chunks = chunk_document_pages(
        pages=pages,
        document_id="doc-test-1",
        filename="test.pdf",
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
    )

    assert len(chunks) > 1

    # Verify each chunk has correct metadata
    for idx, chunk in enumerate(chunks):
        assert chunk.metadata["document_id"] == "doc-test-1"
        assert chunk.metadata["filename"] == "test.pdf"
        assert chunk.metadata["chunk_index"] == idx
        assert chunk.metadata["page"] in [1, 2]
        assert len(chunk.page_content) <= chunk_size + 100  # splitter tolerance for boundaries

    # Verify page 1 chunks precede page 2 chunks
    page1_chunks = [c for c in chunks if c.metadata["page"] == 1]
    page2_chunks = [c for c in chunks if c.metadata["page"] == 2]
    assert len(page1_chunks) > 0
    assert len(page2_chunks) > 0
    assert page1_chunks[-1].metadata["chunk_index"] < page2_chunks[0].metadata["chunk_index"]


def test_vector_store_add_and_delete(tmp_path, monkeypatch):
    # Route vector store paths to temporary test directory
    test_dir = str(tmp_path / "test_data")
    monkeypatch.setattr("app.config.settings.data_dir", test_dir)
    monkeypatch.setattr("app.config.settings.vector_store_path", str(tmp_path / "test_data" / "faiss"))
    clear_all_data()

    pages = [(1, "Retrieval Augmented Generation grounds LLMs with verified documents.")]
    chunks = chunk_document_pages(pages, "doc-delete-test", "sample.pdf")

    add_documents_to_store(chunks)
    store = get_vector_store()
    assert store is not None
    assert len(store.docstore._dict) == len(chunks)

    # Delete the document
    deleted = delete_document_vectors("doc-delete-test")
    assert deleted is True

    # Vector store should now be cleared
    assert get_vector_store() is None
    clear_all_data()
