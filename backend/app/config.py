import os
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

# documind project root is two levels up from backend/app
BASE_DIR = Path(__file__).resolve().parent.parent.parent
ENV_PATH = BASE_DIR / ".env"


class Settings(BaseSettings):
    gemini_api_key: str = ""
    embedding_model_name: str = "all-MiniLM-L6-v2"
    data_dir: str = str(BASE_DIR / "data")
    vector_store_path: str = str(BASE_DIR / "data" / "faiss_index")
    chunk_size: int = 800
    chunk_overlap: int = 150
    top_k: int = 5
    similarity_threshold: float = 0.35
    max_upload_size_mb: int = 10
    cors_origins: str = "http://localhost:5173,http://localhost:3000"

    model_config = SettingsConfigDict(
        env_file=str(ENV_PATH) if ENV_PATH.exists() else None,
        env_file_encoding="utf-8",
        extra="ignore"
    )

    @property
    def cors_origins_list(self) -> list[str]:
        # Split comma-separated origin strings for FastAPI CORSMiddleware
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


# Cached settings instance
settings = Settings()
