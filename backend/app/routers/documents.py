import uuid
from datetime import datetime, timezone
from typing import List
from fastapi import APIRouter, File, HTTPException, Request, UploadFile, status

from app.config import settings
from app.models.schemas import DocumentInfo, DocumentListResponse
from app.security import rate_limiter, sanitize_filename, validate_pdf_file
from app.services.ingestion import chunk_document_pages, parse_pdf_pages
from app.services.vector_store import (
    add_documents_to_store,
    delete_document_metadata,
    delete_document_vectors,
    get_all_documents_metadata,
    save_document_metadata,
)

router = APIRouter(prefix="/api/documents", tags=["documents"])


@router.post("", response_model=DocumentListResponse, status_code=status.HTTP_201_CREATED)
async def upload_documents(
    request: Request,
    files: List[UploadFile] = File(...)
) -> DocumentListResponse:
    # Check rate limiting per client IP
    client_ip = request.client.host if request.client else "127.0.0.1"
    rate_limiter.check(client_ip)

    if not files:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No files uploaded."
        )

    ingested_docs: List[DocumentInfo] = []

    for file in files:
        safe_name = sanitize_filename(file.filename or "document.pdf")
        content = await file.read()

        # Security validation: size limit and magic bytes
        validate_pdf_file(content, safe_name, max_size_mb=settings.max_upload_size_mb)

        # Parse text page by page preserving 1-based page numbers
        pages = parse_pdf_pages(content)
        if not pages or all(len(p[1]) == 0 for p in pages):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File '{safe_name}' has no readable text. Scanned PDFs without OCR are not supported."
            )

        document_id = str(uuid.uuid4())

        # Chunk pages with overlap and document metadata
        chunks = chunk_document_pages(
            pages=pages,
            document_id=document_id,
            filename=safe_name,
            chunk_size=settings.chunk_size,
            chunk_overlap=settings.chunk_overlap,
        )

        # Add chunks into the FAISS vector index
        add_documents_to_store(chunks)

        # Record document metadata
        doc_info = DocumentInfo(
            id=document_id,
            filename=safe_name,
            page_count=len(pages),
            chunk_count=len(chunks),
            upload_timestamp=datetime.now(timezone.utc).isoformat(),
        )
        save_document_metadata(doc_info)
        ingested_docs.append(doc_info)

    return DocumentListResponse(documents=ingested_docs)


@router.get("", response_model=DocumentListResponse)
def list_documents() -> DocumentListResponse:
    # Return all uploaded documents with page and chunk counts
    return DocumentListResponse(documents=get_all_documents_metadata())


@router.delete("/{document_id}")
def delete_document(document_id: str):
    # Remove from catalog and delete vectors from FAISS
    deleted_info = delete_document_metadata(document_id)
    if not deleted_info:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document with ID '{document_id}' not found."
        )

    delete_document_vectors(document_id)
    return {"deleted": True, "id": document_id, "message": "Document deleted successfully"}
