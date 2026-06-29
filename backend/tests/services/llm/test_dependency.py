import pytest
from fastapi import HTTPException

from lastro.core.config import settings
from lastro.services.llm.claude import ClaudeVisionProvider
from lastro.services.llm.dependency import get_llm_provider
from lastro.services.llm.ollama import OllamaProvider


def test_default_retorna_ollama_sem_precisar_de_chave(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "llm_provider", "ollama")

    provider = get_llm_provider()

    assert isinstance(provider, OllamaProvider)


def test_claude_sem_chave_configurada_levanta_400(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "llm_provider", "claude")
    monkeypatch.setattr(settings, "anthropic_api_key", None)

    with pytest.raises(HTTPException) as exc_info:
        get_llm_provider()
    assert exc_info.value.status_code == 400


def test_claude_com_chave_configurada_retorna_claude(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "llm_provider", "claude")
    monkeypatch.setattr(settings, "anthropic_api_key", "fake-key")

    provider = get_llm_provider()

    assert isinstance(provider, ClaudeVisionProvider)
