from fastapi import APIRouter, Request, status
from app.models.schemas import ChatRequest, ChatResponse
from app.security import rate_limiter
from app.services.rag import generate_rag_answer

router = APIRouter(prefix="/api/chat", tags=["chat"])


@router.post("", response_model=ChatResponse, status_code=status.HTTP_200_OK)
def chat_endpoint(request: Request, body: ChatRequest) -> ChatResponse:
    # Check rate limit per client IP
    client_ip = request.client.host if request.client else "127.0.0.1"
    rate_limiter.check(client_ip)

    return generate_rag_answer(
        question=body.question,
        document_ids=body.document_ids,
        history=body.history,
    )
