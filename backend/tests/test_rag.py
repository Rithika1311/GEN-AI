import json
from unittest.mock import MagicMock
import pytest
from langchain_core.messages import AIMessage, AIMessageChunk
from langchain_core.documents import Document
from fastapi.testclient import TestClient

from app.main import app
from app.models.schemas import ChatMessage, SourceCitation
from app.services.rag import (
    NOT_FOUND_MESSAGE,
    format_context_prompt,
    generate_rag_answer,
    rewrite_query_if_needed,
    stream_rag_answer,
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


def test_rewrite_query_with_empty_history():
    # When there is no conversation history, query is unchanged
    q = "What is backpropagation?"
    assert rewrite_query_if_needed(q, []) == q
    assert rewrite_query_if_needed(q, None) == q


def test_rewrite_query_with_history(monkeypatch):
    # Mock LLM to test rewrite query logic
    mock_llm = MagicMock()
    mock_llm.invoke.return_value = AIMessage(
        content="What are the limitations of the Transformer architecture?"
    )
    monkeypatch.setattr("app.services.rag.get_llm", lambda **kwargs: mock_llm)

    history = [
        ChatMessage(role="user", content="Explain Transformer models."),
        ChatMessage(role="assistant", content="Transformers use self-attention."),
    ]
    rewritten = rewrite_query_if_needed("What are its limitations?", history)
    assert rewritten == "What are the limitations of the Transformer architecture?"


def test_rag_out_of_scope_returns_not_found(tmp_path, monkeypatch):
    test_dir = str(tmp_path / "test_data")
    monkeypatch.setattr("app.config.settings.data_dir", test_dir)
    monkeypatch.setattr("app.config.settings.vector_store_path", str(tmp_path / "test_data" / "faiss"))
    clear_all_data()

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

    clear_all_data()


@pytest.mark.asyncio
async def test_stream_rag_answer_events(tmp_path, monkeypatch):
    test_dir = str(tmp_path / "test_data")
    monkeypatch.setattr("app.config.settings.data_dir", test_dir)
    monkeypatch.setattr("app.config.settings.vector_store_path", str(tmp_path / "test_data" / "faiss"))
    monkeypatch.setattr("app.config.settings.similarity_threshold", 0.2)
    clear_all_data()

    docs = [
        Document(
            page_content="Quicksort has an average time complexity of O(n log n).",
            metadata={"document_id": "qs-1", "filename": "sorting.pdf", "page": 2, "chunk_index": 0}
        )
    ]
    add_documents_to_store(docs)

    # Mock streaming chunks
    mock_llm = MagicMock()
    mock_llm.stream.return_value = [
        AIMessageChunk(content="Quicksort runs in "),
        AIMessageChunk(content="O(n log n) [sorting.pdf, p.2]."),
    ]
    monkeypatch.setattr("app.services.rag.get_llm", lambda **kwargs: mock_llm)

    events = []
    async for chunk in stream_rag_answer("What is quicksort complexity?"):
        events.append(chunk)

    full_output = "".join(events)
    assert 'data: {"type": "token", "content": "Quicksort runs in "}' in full_output
    assert 'data: {"type": "token", "content": "O(n log n) [sorting.pdf, p.2]."}' in full_output
    assert 'data: {"type": "sources"' in full_output
    assert 'data: {"type": "done"}' in full_output

    clear_all_data()


def test_chat_endpoint_streaming(tmp_path, monkeypatch):
    test_dir = str(tmp_path / "test_data")
    monkeypatch.setattr("app.config.settings.data_dir", test_dir)
    monkeypatch.setattr("app.config.settings.vector_store_path", str(tmp_path / "test_data" / "faiss"))
    clear_all_data()

    # Empty store streaming response
    res = client.post("/api/chat", json={"question": "What is DocuMind?"})
    assert res.status_code == 200
    assert "text/event-stream" in res.headers["content-type"]
    text = res.text
    assert "data: " in text
    assert "I couldn't find that in the uploaded documents." in text
