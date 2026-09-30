import io
from pypdf import PdfWriter
from fastapi.testclient import TestClient

from app.main import app
from app.services.vector_store import clear_all_data

client = TestClient(app)


def create_sample_pdf_bytes(num_pages: int = 2, text: str = "Test document content") -> bytes:
    writer = PdfWriter()
    for _ in range(num_pages):
        page = writer.add_blank_page(width=300, height=300)
    # pypdf blank pages don't have text streams, so we can craft a minimal valid PDF with a text stream
    # or write text annotations/objects. A clean minimal PDF stream:
    pdf_text = f"%PDF-1.4\n1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>\nendobj\n4 0 obj\n<< /Length 55 >>\nstream\nBT /F1 12 Tf 72 712 Td ({text}) Tj ET\nendstream\nendobj\n5 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\nendobj\nxref\n0 6\n0000000000 65535 f \n0000000009 00000 n \n0000000058 00000 n \n0000000115 00000 n \n0000000244 00000 n \n0000000350 00000 n \ntrailer\n<< /Size 6 /Root 1 0 R >>\nstartxref\n433\n%%EOF\n"
    return pdf_text.encode("latin-1")


def test_documents_crud_flow(tmp_path, monkeypatch):
    test_dir = str(tmp_path / "test_data")
    monkeypatch.setattr("app.config.settings.data_dir", test_dir)
    monkeypatch.setattr("app.config.settings.vector_store_path", str(tmp_path / "test_data" / "faiss"))
    clear_all_data()

    # 1. Initially empty
    list_res = client.get("/api/documents")
    assert list_res.status_code == 200
    assert list_res.json()["documents"] == []

    # 2. Upload valid PDF
    pdf_bytes = create_sample_pdf_bytes(text="DocuMind RAG testing document")
    files = [("files", ("sample_report.pdf", pdf_bytes, "application/pdf"))]
    upload_res = client.post("/api/documents", files=files)
    assert upload_res.status_code == 201
    docs = upload_res.json()["documents"]
    assert len(docs) == 1
    doc_id = docs[0]["id"]
    assert docs[0]["filename"] == "sample_report.pdf"
    assert docs[0]["page_count"] >= 1
    assert docs[0]["chunk_count"] >= 1

    # 3. List contains newly uploaded doc
    list_res = client.get("/api/documents")
    assert list_res.status_code == 200
    catalog = list_res.json()["documents"]
    assert len(catalog) == 1
    assert catalog[0]["id"] == doc_id

    # 4. Delete document
    del_res = client.delete(f"/api/documents/{doc_id}")
    assert del_res.status_code == 200
    assert del_res.json()["deleted"] is True or "deleted" in del_res.json()["message"]

    # 5. List is empty again
    list_res2 = client.get("/api/documents")
    assert list_res2.status_code == 200
    assert list_res2.json()["documents"] == []

    # 6. Deleting non-existent returns 404
    del_res_404 = client.delete("/api/documents/non-existent-id")
    assert del_res_404.status_code == 404

    clear_all_data()


def test_upload_rejection_security(tmp_path, monkeypatch):
    test_dir = str(tmp_path / "test_data")
    monkeypatch.setattr("app.config.settings.data_dir", test_dir)
    monkeypatch.setattr("app.config.settings.vector_store_path", str(tmp_path / "test_data" / "faiss"))
    clear_all_data()

    # Rejection of non-PDF
    bad_file = [("files", ("malicious.exe", b"MZ\x90\x00\x03\x00\x00\x00", "application/octet-stream"))]
    res_bad = client.post("/api/documents", files=bad_file)
    assert res_bad.status_code == 415

    # Rejection of empty / unreadable text PDF
    empty_pdf = b"%PDF-1.4\n%empty\n%%EOF"
    res_empty = client.post("/api/documents", files=[("files", ("empty.pdf", empty_pdf, "application/pdf"))])
    assert res_empty.status_code == 400

    clear_all_data()
