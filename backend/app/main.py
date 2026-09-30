from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.models.schemas import HealthResponse
from app.routers.documents import router as documents_router

app = FastAPI(
    title="DocuMind API",
    description="RAG backend API for document QA with citations",
    version="1.0.0",
)

# CORS configuration restricted to frontend origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(documents_router)


@app.get("/api/health", response_model=HealthResponse)
def health_check() -> HealthResponse:
    # Basic liveness probe to verify API server is responsive
    return HealthResponse(status="ok")
