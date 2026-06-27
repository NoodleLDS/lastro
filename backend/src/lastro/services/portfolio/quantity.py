from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from lastro.models.contribution import Contribution
from lastro.models.position import Position
from lastro.models.sale import Sale
from lastro.models.stock_split import StockSplit
from lastro.services.portfolio.stock_split import adjust_for_splits


def calculate_quantity(
    contributions: list[Contribution],
    sales: list[Sale] | None = None,
    splits: list[StockSplit] | None = None,
) -> float:
    """Quantidade atual derivada do extrato: aportes - vendas, ajustados por
    splits. Nunca um delta acumulado solto — mesmo princípio do preço médio."""
    splits = splits or []
    contribution_events = adjust_for_splits(contributions, splits)
    sale_events = adjust_for_splits(sales or [], splits)

    bought_quantity = sum(e.quantity for e in contribution_events)
    sold_quantity = sum(e.quantity for e in sale_events)
    return bought_quantity - sold_quantity


async def sync_position_quantity(session: AsyncSession, position_id: int) -> None:
    """Recalcula e persiste position.quantity a partir do extrato completo.
    Chamado após qualquer mutação de Contribution/Sale/StockSplit, pra manter
    a coluna armazenada (lida por dashboard/alocação/relatórios) sempre
    coerente com a fonte da verdade — o histórico de eventos."""
    position = await session.get(Position, position_id)
    if position is None:
        return

    contributions_result = await session.exec(
        select(Contribution).where(Contribution.position_id == position_id)
    )
    sales_result = await session.exec(select(Sale).where(Sale.position_id == position_id))
    splits_result = await session.exec(
        select(StockSplit).where(StockSplit.position_id == position_id)
    )

    position.quantity = calculate_quantity(
        list(contributions_result.all()), list(sales_result.all()), list(splits_result.all())
    )
    session.add(position)
