from fastapi import APIRouter, Depends, HTTPException
from sqlmodel.ext.asyncio.session import AsyncSession

from lastro.core.master_prompt import MASTER_PROMPT
from lastro.db import get_session
from lastro.schemas.analyst import AskAnalystRequest, AskAnalystResponse
from lastro.services.analytics.analyst_context import build_portfolio_context
from lastro.services.llm.dependency import get_ollama_provider
from lastro.services.llm.provider import LLMProvider

router = APIRouter(prefix="/analyst", tags=["analyst"])


@router.post("/ask", response_model=AskAnalystResponse)
async def ask_analyst(
    payload: AskAnalystRequest,
    session: AsyncSession = Depends(get_session),
    llm: LLMProvider = Depends(get_ollama_provider),
) -> AskAnalystResponse:
    if not payload.question.strip():
        raise HTTPException(status_code=422, detail="pergunta vazia")

    portfolio_context = await build_portfolio_context(session)
    system_prompt = (
        f"{MASTER_PROMPT}\n\n# Dados vivos do banco (use estes números)\n\n{portfolio_context}"
    )

    answer = await llm.complete(system_prompt, payload.question)
    return AskAnalystResponse(answer=answer)
