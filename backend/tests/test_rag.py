from unittest.mock import MagicMock
from langchain_core.messages import AIMessage
from langchain_core.documents import Document
from fastapi.testclient import TestClient

from app.main import app
from app.models.schemas import SourceCitation
from app.services.rag import (
    NOT_FOUND_MESSAGE,
    format_context_prompt,
    generate_rag_answer,
)
from app.services.vector_store import add_documents_to_store, clear_all_data

client = TestClient(app)


def test_format_context_prompt_wrapping():
    citation = SourceCitation(
        document_id="d1",
        filename="notes.pdf",
        page=3,
        chunk_index=0,
        text="A hash table provides O(1) average lookup time.",
        similarity_score=0.92,
    )
    formatted = format_context_prompt([citation])
    assert "<context>" in formatted
    assert "</context>" in formatted
    assert '<passage file="notes.pdf" page="3">' in formatted
    assert "A hash table provides O(1) average lookup time." in formatted


def test_rag_out_of_scope_returns_not_found(tmp_path, monkeypatch):
    test_dir = str(tmp_path / "test_data")
    monkeypatch.setattr("app.config.settings.data_dir", test_dir)
    monkeypatch.setattr("app.config.settings.vector_store_path", str(tmp_path / "test_data" / "faiss"))
    clear_all_data()

    # Empty store -> should return not found message immediately without calling LLM
    response = generate_rag_answer(question="What is the speed of light?")
    assert response.answer == NOT_FOUND_MESSAGE
    assert len(response.sources) == 0


def test_rag_answer_with_mocked_llm(tmp_path, monkeypatch):
    test_dir = str(tmp_path / "test_data")
    monkeypatch.setattr("app.config.settings.data_dir", test_dir)
    monkeypatch.setattr("app.config.settings.vector_store_path", str(tmp_path / "test_data" / "faiss"))
    monkeypatch.setattr("app.config.settings.similarity_threshold", 0.2)
    clear_all_data()

    docs = [
        Document(
            page_content="Binary search runs in logarithmic time O(log n).",
            metadata={"document_id": "algo-1", "filename": "dsa.pdf", "page": 4, "chunk_index": 0}
        )
    ]
    add_documents_to_store(docs)

    # Mock the LLM to verify pipeline without requiring API calls in tests
    mock_llm = MagicMock()
    mock_llm.invoke.return_value = AIMessage(
        content="Binary search runs in O(log n) time [dsa.pdf, p.4]."
    )
    monkeypatch.setattr("app.services.rag.get_llm", lambda **kwargs: mock_llm)

    response = generate_rag_answer(question="What is the time complexity of binary search?")
    assert "O(log n)" in response.answer
    assert len(response.sources) > 0
    assert response.sources[0].filename == "dsa.pdf"
    assert response.sources[0].page == 4

    # Verify LLM was called with the system prompt and context
    call_args = mock_llm.invoke.call_args[0][0]
    system_msg = call_args[0].content
    human_msg = call_args[1].content
    assert "DocuMind" in system_msg
    assert "<context>" in human_msg
    assert "Binary search runs in logarithmic time" in human_msg

    clear_all_data()


def test_chat_endpoint_integration(tmp_path, monkeypatch):
    test_dir = str(tmp_path / "test_data")
    monkeypatch.setattr("app.config.settings.data_dir", test_dir)
    monkeypatch.setattr("app.config.settings.vector_store_path", str(tmp_path / "test_data" / "faiss"))
    clear_all_data()

    res = client.post("/api/chat", json={"question": "What is DocuMind?"})
    assert res.status_code == 200
    data = res.json()
    assert "answer" in data
    assert "sources" in data
