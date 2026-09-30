from typing import List, Optional
from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str = "ok"


class DocumentInfo(BaseModel):
    id: str
    filename: str
    page_count: int
    chunk_count: int
    upload_timestamp: str


class DocumentListResponse(BaseModel):
    documents: List[DocumentInfo]


class ChatMessage(BaseModel):
    role: str = Field(..., description="Role: 'user' or 'assistant'")
    content: str = Field(..., description="Message text")


class ChatRequest(BaseModel):
    question: str = Field(..., min_length=1, description="Question asked by the user")
    document_ids: Optional[List[str]] = Field(default=None, description="Optional document IDs to filter search")
    history: List[ChatMessage] = Field(default_factory=list, description="Prior conversation messages")


class SourceCitation(BaseModel):
    document_id: str
    filename: str
    page: int
    chunk_index: int
    text: str
    similarity_score: float


class ChatResponse(BaseModel):
    answer: str
    sources: List[SourceCitation]
