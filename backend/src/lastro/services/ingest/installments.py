import calendar
from datetime import date

from sqlmodel.ext.asyncio.session import AsyncSession

from lastro.models.transaction import Transaction


def _add_months(d: date, months: int) -> date:
    month_index = d.month - 1 + months
    year = d.year + month_index // 12
    month = month_index % 12 + 1
    day = min(d.day, calendar.monthrange(year, month)[1])
    return date(year, month, day)


async def project_installments(session: AsyncSession, first: Transaction) -> list[Transaction]:
    """Cria as parcelas futuras (current+1 até total) a partir de `first`,
    todas ligadas por parent_id à transação raiz informada."""
    if first.installment_current is None or first.installment_total is None:
        return []

    parent_id = first.parent_id if first.parent_id is not None else first.id

    created: list[Transaction] = []
    for installment_current in range(first.installment_current + 1, first.installment_total + 1):
        months_ahead = installment_current - first.installment_current
        transaction = Transaction(
            date=_add_months(first.date, months_ahead),
            description=first.description,
            amount_cents=first.amount_cents,
            card_id=first.card_id,
            category_id=first.category_id,
            source=first.source,
            status=first.status,
            installment_current=installment_current,
            installment_total=first.installment_total,
            parent_id=parent_id,
        )
        session.add(transaction)
        created.append(transaction)

    if created:
        await session.flush()

    return created
