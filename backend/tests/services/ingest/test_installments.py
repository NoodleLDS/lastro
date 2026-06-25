from datetime import date

from sqlmodel.ext.asyncio.session import AsyncSession

from lastro.models.card import Card
from lastro.models.transaction import Transaction
from lastro.services.ingest.installments import _add_months, project_installments


def test_add_months_caso_simples() -> None:
    assert _add_months(date(2026, 1, 15), 1) == date(2026, 2, 15)


def test_add_months_virada_de_ano() -> None:
    assert _add_months(date(2026, 12, 1), 2) == date(2027, 2, 1)


def test_add_months_dia_31_em_mes_de_30_dias() -> None:
    assert _add_months(date(2026, 1, 31), 1) == date(2026, 2, 28)


def test_add_months_dia_31_para_fevereiro_bissexto() -> None:
    assert _add_months(date(2028, 1, 31), 1) == date(2028, 2, 29)


async def _create_card(session: AsyncSession) -> Card:
    card = Card(name="Teste")
    session.add(card)
    await session.flush()
    return card


async def test_projeta_parcelas_seguintes_a_partir_do_meio(session: AsyncSession) -> None:
    card = await _create_card(session)
    first = Transaction(
        date=date(2026, 6, 10),
        description="tablet",
        amount_cents=33598,
        card_id=card.id,
        installment_current=3,
        installment_total=9,
    )
    session.add(first)
    await session.flush()

    created = await project_installments(session, first)

    assert [t.installment_current for t in created] == [4, 5, 6, 7, 8, 9]
    assert [t.date for t in created] == [
        date(2026, 7, 10),
        date(2026, 8, 10),
        date(2026, 9, 10),
        date(2026, 10, 10),
        date(2026, 11, 10),
        date(2026, 12, 10),
    ]
    assert all(t.parent_id == first.id for t in created)
    assert all(t.amount_cents == first.amount_cents for t in created)
    assert all(t.card_id == card.id for t in created)


async def test_nao_projeta_quando_sem_parcela(session: AsyncSession) -> None:
    card = await _create_card(session)
    first = Transaction(
        date=date(2026, 6, 10),
        description="zebu",
        amount_cents=2200,
        card_id=card.id,
    )
    session.add(first)
    await session.flush()

    created = await project_installments(session, first)

    assert created == []


async def test_parent_id_usa_raiz_quando_first_ja_e_uma_parcela(session: AsyncSession) -> None:
    card = await _create_card(session)
    root = Transaction(
        date=date(2026, 1, 10),
        description="tablet",
        amount_cents=10000,
        card_id=card.id,
        installment_current=1,
        installment_total=3,
    )
    session.add(root)
    await session.flush()

    second = Transaction(
        date=date(2026, 2, 10),
        description="tablet",
        amount_cents=10000,
        card_id=card.id,
        installment_current=2,
        installment_total=3,
        parent_id=root.id,
    )
    session.add(second)
    await session.flush()

    created = await project_installments(session, second)

    assert len(created) == 1
    assert created[0].installment_current == 3
    assert created[0].parent_id == root.id
