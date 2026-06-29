import json
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from lastro.core.master_prompt import MASTER_PROMPT
from lastro.db import get_session
from lastro.models.analyst_instructions import AnalystInstructions
from lastro.models.conversation import Conversation, Message, MessageRole
from lastro.schemas.analyst import (
    AnalystInstructionsRead,
    AnalystInstructionsUpdate,
    AnalystMemoryRead,
    AskAnalystRequest,
    AskAnalystResponse,
)
from lastro.schemas.conversation import ConversationRead, ConversationUpdate, MessageRead
from lastro.services.analytics.analyst_context import build_portfolio_context
from lastro.services.llm.dependency import get_ollama_provider
from lastro.services.llm.ollama import OllamaProvider
from lastro.services.llm.provider import ChatMessage, LLMProvider

router = APIRouter(prefix="/analyst", tags=["analyst"])


async def _build_system_prompt(session: AsyncSession) -> str:
    portfolio_context = await build_portfolio_context(session)
    instructions = await session.exec(select(AnalystInstructions))
    custom_instructions = instructions.first()
    prompt = f"{MASTER_PROMPT}\n\n# Dados vivos do banco (use estes números)\n\n{portfolio_context}"
    if custom_instructions and custom_instructions.content.strip():
        prompt += f"\n\n# Instruções adicionais do usuário\n\n{custom_instructions.content}"
    return prompt


async def _get_or_create_conversation(
    session: AsyncSession, conversation_id: int | None, title_hint: str
) -> Conversation:
    if conversation_id is not None:
        conversation = await session.get(Conversation, conversation_id)
        if conversation is None:
            raise HTTPException(status_code=404, detail="conversa não encontrada")
        return conversation

    title = title_hint.strip()[:60] or "Nova conversa"
    conversation = Conversation(title=title)
    session.add(conversation)
    await session.commit()
    await session.refresh(conversation)
    return conversation


async def _load_history(session: AsyncSession, conversation_id: int) -> list[ChatMessage]:
    result = await session.exec(
        select(Message).where(Message.conversation_id == conversation_id).order_by(Message.id)
    )
    return [{"role": m.role.value, "content": m.content} for m in result.all()]


async def _save_message(
    session: AsyncSession,
    conversation_id: int,
    role: MessageRole,
    content: str,
    model: str | None = None,
    tokens_per_second: float | None = None,
) -> None:
    session.add(
        Message(
            conversation_id=conversation_id,
            role=role,
            content=content,
            model=model,
            tokens_per_second=tokens_per_second,
        )
    )
    conversation = await session.get(Conversation, conversation_id)
    if conversation is not None:
        conversation.updated_at = datetime.now(UTC)
        session.add(conversation)
    await session.commit()


@router.post("/ask", response_model=AskAnalystResponse)
async def ask_analyst(
    payload: AskAnalystRequest,
    session: AsyncSession = Depends(get_session),
    llm: LLMProvider = Depends(get_ollama_provider),
) -> AskAnalystResponse:
    if not payload.question.strip():
        raise HTTPException(status_code=422, detail="pergunta vazia")

    conversation = await _get_or_create_conversation(
        session, payload.conversation_id, payload.question
    )
    conversation_id = conversation.id
    history = await _load_history(session, conversation_id)
    system_prompt = await _build_system_prompt(session)

    await _save_message(session, conversation_id, MessageRole.USER, payload.question)
    answer = await llm.complete(system_prompt, payload.question, history)
    await _save_message(session, conversation_id, MessageRole.ASSISTANT, answer)

    return AskAnalystResponse(answer=answer, conversation_id=conversation_id)


@router.post("/ask/stream")
async def ask_analyst_stream(
    payload: AskAnalystRequest,
    session: AsyncSession = Depends(get_session),
    llm: OllamaProvider = Depends(get_ollama_provider),
) -> StreamingResponse:
    if not payload.question.strip():
        raise HTTPException(status_code=422, detail="pergunta vazia")

    conversation = await _get_or_create_conversation(
        session, payload.conversation_id, payload.question
    )
    conversation_id = conversation.id
    history = await _load_history(session, conversation_id)
    system_prompt = await _build_system_prompt(session)

    await _save_message(session, conversation_id, MessageRole.USER, payload.question)

    async def event_stream():
        full_answer = ""
        last_model: str | None = None
        last_tps: float | None = None
        yield f"data: {json.dumps({'conversation_id': conversation_id})}\n\n"
        async for chunk in llm.complete_stream(system_prompt, payload.question, history):
            full_answer += chunk.content
            last_model = chunk.model or last_model
            last_tps = chunk.tokens_per_second or last_tps
            data = {
                "content": chunk.content,
                "done": chunk.done,
                "model": chunk.model,
                "tokens_per_second": chunk.tokens_per_second,
            }
            yield f"data: {json.dumps(data)}\n\n"
        await _save_message(
            session, conversation_id, MessageRole.ASSISTANT, full_answer, last_model, last_tps
        )

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@router.get("/memory", response_model=AnalystMemoryRead)
async def get_memory(session: AsyncSession = Depends(get_session)) -> AnalystMemoryRead:
    portfolio_context = await build_portfolio_context(session)
    return AnalystMemoryRead(master_prompt=MASTER_PROMPT, portfolio_context=portfolio_context)


@router.get("/instructions", response_model=AnalystInstructionsRead)
async def get_instructions(session: AsyncSession = Depends(get_session)) -> AnalystInstructions:
    result = await session.exec(select(AnalystInstructions))
    instructions = result.first()
    return instructions or AnalystInstructions(content="")


@router.put("/instructions", response_model=AnalystInstructionsRead)
async def update_instructions(
    payload: AnalystInstructionsUpdate, session: AsyncSession = Depends(get_session)
) -> AnalystInstructions:
    result = await session.exec(select(AnalystInstructions))
    instructions = result.first()
    if instructions is None:
        instructions = AnalystInstructions(content=payload.content)
    else:
        instructions.content = payload.content
    session.add(instructions)
    await session.commit()
    await session.refresh(instructions)
    return instructions


@router.get("/conversations", response_model=list[ConversationRead])
async def list_conversations(session: AsyncSession = Depends(get_session)) -> list[Conversation]:
    result = await session.exec(select(Conversation).order_by(Conversation.updated_at.desc()))
    return list(result.all())


@router.get("/conversations/{conversation_id}/messages", response_model=list[MessageRead])
async def list_messages(
    conversation_id: int, session: AsyncSession = Depends(get_session)
) -> list[Message]:
    conversation = await session.get(Conversation, conversation_id)
    if conversation is None:
        raise HTTPException(status_code=404, detail="conversa não encontrada")
    result = await session.exec(
        select(Message).where(Message.conversation_id == conversation_id).order_by(Message.id)
    )
    return list(result.all())


@router.patch("/conversations/{conversation_id}", response_model=ConversationRead)
async def rename_conversation(
    conversation_id: int,
    payload: ConversationUpdate,
    session: AsyncSession = Depends(get_session),
) -> Conversation:
    conversation = await session.get(Conversation, conversation_id)
    if conversation is None:
        raise HTTPException(status_code=404, detail="conversa não encontrada")
    conversation.title = payload.title
    session.add(conversation)
    await session.commit()
    await session.refresh(conversation)
    return conversation


@router.delete("/conversations/{conversation_id}", status_code=204)
async def delete_conversation(
    conversation_id: int, session: AsyncSession = Depends(get_session)
) -> None:
    conversation = await session.get(Conversation, conversation_id)
    if conversation is None:
        raise HTTPException(status_code=404, detail="conversa não encontrada")
    messages = await session.exec(select(Message).where(Message.conversation_id == conversation_id))
    for message in messages.all():
        await session.delete(message)
    await session.delete(conversation)
    await session.commit()
