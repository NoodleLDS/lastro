from fastapi import HTTPException

from lastro.core.config import settings
from lastro.services.llm.claude import ClaudeVisionProvider
from lastro.services.llm.ollama import OllamaProvider
from lastro.services.llm.provider import LLMProvider


def get_llm_provider() -> LLMProvider:
    if not settings.anthropic_api_key:
        raise HTTPException(
            status_code=400,
            detail="recurso opt-in, configure LASTRO_ANTHROPIC_API_KEY",
        )
    return ClaudeVisionProvider(settings.anthropic_api_key)


def get_ollama_provider() -> LLMProvider:
    """Provider default (Ollama local) — usado tanto para categorização de
    transações quanto para o chat do analista. Camada de IA é uma só."""
    return OllamaProvider(settings.ollama_url, settings.ollama_model)
