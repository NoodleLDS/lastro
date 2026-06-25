from datetime import date as date_

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlmodel import func, select
from sqlmodel.ext.asyncio.session import AsyncSession

from lastro.db import get_session
from lastro.models.category import Category
from lastro.models.transaction import (
    CategorizedBy,
    Transaction,
    TransactionSource,
    TransactionStatus,
)
from lastro.schemas.transaction import (
    CategorizationStats,
    ConfirmBatchRequest,
    QuickEntryCreate,
    QuickEntryResult,
    TransactionRead,
    TransactionUpdate,
)
from lastro.services.ingest.categorization import (
    categorize_with_llm,
    find_category_by_rule,
    learn_rule,
)
from lastro.services.ingest.installments import project_installments
from lastro.services.ingest.quick_entry import QuickEntryParseError, parse_quick_entry
from lastro.services.llm.dependency import get_llm_provider, get_ollama_provider
from lastro.services.llm.provider import LLMProvider

router = APIRouter(prefix="/transactions", tags=["transactions"])


async def _resolve_category_id(
    session: AsyncSession,
    category_name: str | None,
    description: str,
    categorization_llm: LLMProvider,
    categorized_by_when_named: CategorizedBy = CategorizedBy.MANUAL,
) -> tuple[int | None, CategorizedBy]:
    if category_name is not None:
        statement = select(Category).where(func.lower(Category.name) == category_name.lower())
        result = await session.exec(statement)
        category = result.first()
        if category is None:
            category = Category(name=category_name)
            session.add(category)
            await session.flush()
        return category.id, categorized_by_when_named

    matched = await find_category_by_rule(session, description)
    if matched is not None:
        return matched.id, CategorizedBy.RULE

    via_llm = await categorize_with_llm(session, categorization_llm, description)
    if via_llm is not None:
        return via_llm.id, CategorizedBy.LLM
    return None, CategorizedBy.NONE


@router.get("", response_model=list[TransactionRead])
async def list_transactions(
    card_id: int | None = None,
    year: int | None = None,
    month: int | None = None,
    status: TransactionStatus = TransactionStatus.CONFIRMED,
    session: AsyncSession = Depends(get_session),
) -> list[Transaction]:
    statement = select(Transaction).where(Transaction.status == status)

    if card_id is not None:
        statement = statement.where(Transaction.card_id == card_id)
    if year is not None:
        statement = statement.where(func.strftime("%Y", Transaction.date) == f"{year:04d}")
    if month is not None:
        statement = statement.where(func.strftime("%m", Transaction.date) == f"{month:02d}")

    statement = statement.order_by(Transaction.date)
    result = await session.exec(statement)
    return list(result.all())


@router.get("/categorization-stats", response_model=CategorizationStats)
async def get_categorization_stats(
    year: int | None = None,
    month: int | None = None,
    session: AsyncSession = Depends(get_session),
) -> CategorizationStats:
    statement = select(Transaction)
    if year is not None:
        statement = statement.where(func.strftime("%Y", Transaction.date) == f"{year:04d}")
    if month is not None:
        statement = statement.where(func.strftime("%m", Transaction.date) == f"{month:02d}")

    result = await session.exec(statement)
    transactions = result.all()

    by_rule = sum(1 for t in transactions if t.categorized_by == CategorizedBy.RULE)
    by_llm = sum(1 for t in transactions if t.categorized_by == CategorizedBy.LLM)
    by_manual = sum(1 for t in transactions if t.categorized_by == CategorizedBy.MANUAL)
    uncategorized = sum(1 for t in transactions if t.categorized_by == CategorizedBy.NONE)
    total = len(transactions)

    resolved_without_ai_pct = (by_rule + by_manual) / total * 100 if total > 0 else None

    return CategorizationStats(
        total=total,
        by_rule=by_rule,
        by_llm=by_llm,
        by_manual=by_manual,
        uncategorized=uncategorized,
        resolved_without_ai_pct=resolved_without_ai_pct,
    )


@router.post("/quick-entry", response_model=QuickEntryResult, status_code=201)
async def create_quick_entry(
    payload: QuickEntryCreate,
    session: AsyncSession = Depends(get_session),
    categorization_llm: LLMProvider = Depends(get_ollama_provider),
) -> QuickEntryResult:
    try:
        parsed = parse_quick_entry(payload.raw)
    except QuickEntryParseError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    category_id, categorized_by = await _resolve_category_id(
        session, parsed.category_name, parsed.description, categorization_llm
    )

    transaction = Transaction(
        date=payload.date,
        description=parsed.description,
        amount_cents=parsed.amount_cents,
        card_id=payload.card_id,
        category_id=category_id,
        categorized_by=categorized_by,
        source=TransactionSource.MANUAL,
        status=TransactionStatus.CONFIRMED,
        installment_current=parsed.installment_current,
        installment_total=parsed.installment_total,
    )
    session.add(transaction)
    await session.flush()

    installments = await project_installments(session, transaction)

    await session.commit()
    await session.refresh(transaction)
    for installment in installments:
        await session.refresh(installment)

    return QuickEntryResult(transaction=transaction, installments=installments)


@router.patch("/{transaction_id}", response_model=TransactionRead)
async def update_transaction(
    transaction_id: int,
    payload: TransactionUpdate,
    session: AsyncSession = Depends(get_session),
) -> Transaction:
    transaction = await session.get(Transaction, transaction_id)
    if transaction is None:
        raise HTTPException(status_code=404, detail="transação não encontrada")

    updates = payload.model_dump(exclude_unset=True)
    had_no_category = transaction.category_id is None

    for field, value in updates.items():
        setattr(transaction, field, value)

    if "category_id" in updates and updates["category_id"] is not None:
        transaction.categorized_by = CategorizedBy.MANUAL
        if had_no_category:
            await learn_rule(session, transaction.description, updates["category_id"])

    session.add(transaction)
    await session.commit()
    await session.refresh(transaction)
    return transaction


@router.delete("/{transaction_id}", status_code=204)
async def delete_transaction(
    transaction_id: int, session: AsyncSession = Depends(get_session)
) -> None:
    transaction = await session.get(Transaction, transaction_id)
    if transaction is None:
        raise HTTPException(status_code=404, detail="transação não encontrada")

    children_result = await session.exec(
        select(Transaction).where(Transaction.parent_id == transaction_id)
    )
    for child in children_result.all():
        await session.delete(child)

    await session.delete(transaction)
    await session.commit()


@router.post("/vision-preview", response_model=list[TransactionRead], status_code=201)
async def create_vision_preview(
    card_id: int,
    file: UploadFile = File(...),
    session: AsyncSession = Depends(get_session),
    llm: LLMProvider = Depends(get_llm_provider),
    categorization_llm: LLMProvider = Depends(get_ollama_provider),
) -> list[Transaction]:
    image_bytes = await file.read()
    mime_type = file.content_type or "image/png"

    items = await llm.vision(image_bytes, mime_type)

    created: list[Transaction] = []
    for item in items:
        if item.suggested_category is not None:
            category_id, categorized_by = await _resolve_category_id(
                session,
                item.suggested_category,
                item.description,
                categorization_llm,
                categorized_by_when_named=CategorizedBy.LLM,
            )
        else:
            matched = await find_category_by_rule(session, item.description)
            if matched is not None:
                category_id, categorized_by = matched.id, CategorizedBy.RULE
            else:
                via_llm = await categorize_with_llm(session, categorization_llm, item.description)
                if via_llm is not None:
                    category_id, categorized_by = via_llm.id, CategorizedBy.LLM
                else:
                    category_id, categorized_by = None, CategorizedBy.NONE

        transaction = Transaction(
            date=item.date or date_.today(),
            description=item.description,
            amount_cents=item.amount_cents,
            card_id=card_id,
            category_id=category_id,
            categorized_by=categorized_by,
            source=TransactionSource.VISION_PREVIEW,
            status=TransactionStatus.PENDING_REVIEW,
        )
        session.add(transaction)
        created.append(transaction)

    await session.commit()
    for transaction in created:
        await session.refresh(transaction)

    return created


@router.post("/{transaction_id}/confirm", response_model=TransactionRead)
async def confirm_transaction(
    transaction_id: int, session: AsyncSession = Depends(get_session)
) -> Transaction:
    transaction = await session.get(Transaction, transaction_id)
    if transaction is None:
        raise HTTPException(status_code=404, detail="transação não encontrada")

    transaction.status = TransactionStatus.CONFIRMED
    session.add(transaction)
    await session.flush()

    await project_installments(session, transaction)

    await session.commit()
    await session.refresh(transaction)
    return transaction


@router.post("/confirm-batch", response_model=list[TransactionRead])
async def confirm_transactions_batch(
    payload: ConfirmBatchRequest, session: AsyncSession = Depends(get_session)
) -> list[Transaction]:
    confirmed: list[Transaction] = []
    for transaction_id in payload.ids:
        transaction = await session.get(Transaction, transaction_id)
        if transaction is None:
            continue

        transaction.status = TransactionStatus.CONFIRMED
        session.add(transaction)
        await session.flush()
        await project_installments(session, transaction)
        confirmed.append(transaction)

    await session.commit()
    for transaction in confirmed:
        await session.refresh(transaction)

    return confirmed
