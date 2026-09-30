import io
import re
from typing import List, Tuple
from pypdf import PdfReader
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.config import settings


def clean_text(text: str) -> str:
    # Remove null bytes and carriage returns
    text = text.replace("\x00", " ").replace("\r", " ")
    # Replace multiple horizontal spaces with a single space
    text = re.sub(r"[ \t]+", " ", text)
    # Replace more than two consecutive newlines with two
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def parse_pdf_pages(file_bytes: bytes) -> List[Tuple[int, str]]:
    # Extract text page-by-page preserving 1-based page numbers
    reader = PdfReader(io.BytesIO(file_bytes))
    pages: List[Tuple[int, str]] = []
    for idx, page in enumerate(reader.pages):
        page_number = idx + 1
        raw_text = page.extract_text() or ""
        cleaned = clean_text(raw_text)
        pages.append((page_number, cleaned))
    return pages


def chunk_document_pages(
    pages: List[Tuple[int, str]],
    document_id: str,
    filename: str,
    chunk_size: int = settings.chunk_size,
    chunk_overlap: int = settings.chunk_overlap,
) -> List[Document]:
    # Split text while preserving page number and document metadata on each chunk
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", ". ", " ", ""],
    )

    documents: List[Document] = []
    chunk_index = 0

    for page_number, page_text in pages:
        if not page_text:
            continue
        page_chunks = splitter.split_text(page_text)
        for chunk in page_chunks:
            chunk_cleaned = chunk.strip()
            if not chunk_cleaned:
                continue
            doc = Document(
                page_content=chunk_cleaned,
                metadata={
                    "document_id": document_id,
                    "filename": filename,
                    "page": page_number,
                    "chunk_index": chunk_index,
                },
            )
            documents.append(doc)
            chunk_index += 1

    return documents
