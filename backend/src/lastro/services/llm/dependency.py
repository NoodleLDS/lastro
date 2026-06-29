from fastapi import HTTPException

from lastro.core.config import settings
from lastro.services.llm.claude import ClaudeVisionProvider
from lastro.services.llm.ollama import OllamaProvider
from lastro.services.llm.provider import LLMProvider


def get_llm_provider() -> LLMProvider:
    """Provider de visão de fatura. Default: Ollama local (sem custo). Opt-in:
    Claude API, ativado via LASTRO_LLM_PROVIDER=claude + LASTRO_ANTHROPIC_API_KEY."""
    if settings.llm_provider == "claude":
        if not settings.anthropic_api_key:
            raise HTTPException(
                status_code=400,
                detail="LASTRO_LLM_PROVIDER=claude requer LASTRO_ANTHROPIC_API_KEY",
            )
        return ClaudeVisionProvider(settings.anthropic_api_key)
    return get_ollama_provider()


def get_ollama_provider() -> LLMProvider:
    """Provider default (Ollama local) — usado tanto para categorização de
    transações quanto para o chat do analista. Camada de IA é uma só."""
    return OllamaProvider(settings.ollama_url, settings.ollama_model, settings.ollama_vision_model)
