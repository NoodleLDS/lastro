import json

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlmodel.ext.asyncio.session import AsyncSession

from lastro.core.master_prompt import MASTER_PROMPT
from lastro.db import get_session
from lastro.schemas.analyst import AskAnalystRequest, AskAnalystResponse
from lastro.services.analytics.analyst_context import build_portfolio_context
from lastro.services.llm.dependency import get_ollama_provider
from lastro.services.llm.ollama import OllamaProvider
from lastro.services.llm.provider import LLMProvider

router = APIRouter(prefix="/analyst", tags=["analyst"])


async def _build_system_prompt(session: AsyncSession) -> str:
    portfolio_context = await build_portfolio_context(session)
    return f"{MASTER_PROMPT}\n\n# Dados vivos do banco (use estes números)\n\n{portfolio_context}"


@router.post("/ask", response_model=AskAnalystResponse)
async def ask_analyst(
    payload: AskAnalystRequest,
    session: AsyncSession = Depends(get_session),
    llm: LLMProvider = Depends(get_ollama_provider),
) -> AskAnalystResponse:
    if not payload.question.strip():
        raise HTTPException(status_code=422, detail="pergunta vazia")

    system_prompt = await _build_system_prompt(session)
    answer = await llm.complete(system_prompt, payload.question)
    return AskAnalystResponse(answer=answer)


@router.post("/ask/stream")
async def ask_analyst_stream(
    payload: AskAnalystRequest,
    session: AsyncSession = Depends(get_session),
    llm: OllamaProvider = Depends(get_ollama_provider),
) -> StreamingResponse:
    if not payload.question.strip():
        raise HTTPException(status_code=422, detail="pergunta vazia")

    system_prompt = await _build_system_prompt(session)

    async def event_stream():
        async for chunk in llm.complete_stream(system_prompt, payload.question):
            data = {
                "content": chunk.content,
                "done": chunk.done,
                "model": chunk.model,
                "tokens_per_second": chunk.tokens_per_second,
            }
            yield f"data: {json.dumps(data)}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")
