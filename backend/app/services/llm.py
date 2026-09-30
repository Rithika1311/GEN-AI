from langchain_core.language_models.chat_models import BaseChatModel
from langchain_google_genai import ChatGoogleGenerativeAI
from app.config import settings


def get_llm(temperature: float = 0.0, streaming: bool = False) -> BaseChatModel:
    # Wrap Gemini API behind a clean interface so the underlying model or provider can be easily swapped
    return ChatGoogleGenerativeAI(
        model=settings.gemini_model,
        google_api_key=settings.gemini_api_key,
        temperature=temperature,
        streaming=streaming,
    )
