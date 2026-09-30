from fastapi import APIRouter, Header, Query, Request, status
from fastapi.responses import StreamingResponse
from app.models.schemas import ChatRequest, ChatResponse
from app.security import rate_limiter
from app.services.rag import generate_rag_answer, stream_rag_answer

router = APIRouter(prefix="/api/chat", tags=["chat"])


@router.post("", status_code=status.HTTP_200_OK)
async def chat_endpoint(
    request: Request,
    body: ChatRequest,
    stream: bool = Query(default=True, description="Stream answer via Server-Sent Events"),
    accept: str = Header(default="text/event-stream"),
):
    # Check rate limit per client IP
    client_ip = request.client.host if request.client else "127.0.0.1"
    rate_limiter.check(client_ip)

    # If stream is disabled or client explicitly asks for application/json only
    if not stream or "application/json" in accept and "text/event-stream" not in accept:
        return generate_rag_answer(
            question=body.question,
            document_ids=body.document_ids,
            history=body.history,
        )

    # Return Server-Sent Events stream
    return StreamingResponse(
        stream_rag_answer(
            question=body.question,
            document_ids=body.document_ids,
            history=body.history,
        ),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )
