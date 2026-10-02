from pathlib import Path
from unittest.mock import MagicMock
from langchain_core.messages import AIMessage
from fastapi.testclient import TestClient

from app.main import app
from app.services.vector_store import clear_all_data

client = TestClient(app)


def test_end_to_end_integration_flow(tmp_path, monkeypatch):
    # Route vector store and data directory to temporary folder
    test_dir = str(tmp_path / "test_data")
    monkeypatch.setattr("app.config.settings.data_dir", test_dir)
    monkeypatch.setattr("app.config.settings.vector_store_path", str(tmp_path / "test_data" / "faiss"))
    monkeypatch.setattr("app.config.settings.similarity_threshold", 0.3)
    clear_all_data()

    # Locate the generated sample PDF
    project_root = Path(__file__).resolve().parent.parent.parent
    sample_pdf_path = project_root / "eval" / "sample.pdf"
    assert sample_pdf_path.exists(), f"sample.pdf not found at {sample_pdf_path}"

    with open(sample_pdf_path, "rb") as f:
        pdf_bytes = f.read()

    # 1. Upload sample.pdf to the documents endpoint
    files = [("files", ("sample.pdf", pdf_bytes, "application/pdf"))]
    upload_res = client.post("/api/documents", files=files)
    assert upload_res.status_code == 201, upload_res.text
    uploaded_docs = upload_res.json()["documents"]
    assert len(uploaded_docs) == 1
    assert uploaded_docs[0]["filename"] == "sample.pdf"
    assert uploaded_docs[0]["page_count"] == 5
    assert uploaded_docs[0]["chunk_count"] > 0

    # 2. Mock the LLM so the test runs completely offline without external network dependency
    mock_llm = MagicMock()
    mock_llm.invoke.return_value = AIMessage(
        content="Raft uses randomized election timers to select cluster leaders [sample.pdf, p.1]."
    )
    monkeypatch.setattr("app.services.rag.get_llm", lambda **kwargs: mock_llm)

    # 3. Ask question via non-streaming POST /api/chat (stream=false)
    chat_payload = {
        "question": "How does the Raft consensus algorithm handle leader election?",
        "history": [],
    }
    chat_res = client.post("/api/chat?stream=false", json=chat_payload)
    assert chat_res.status_code == 200, chat_res.text
    data = chat_res.json()

    # 4. Verify answer text and returned sources
    assert "Raft" in data["answer"]
    assert len(data["sources"]) > 0

    # Check that sources cite the correct file and page 1
    source_pages = [s["page"] for s in data["sources"]]
    source_files = [s["filename"] for s in data["sources"]]
    assert 1 in source_pages
    assert "sample.pdf" in source_files

    clear_all_data()
