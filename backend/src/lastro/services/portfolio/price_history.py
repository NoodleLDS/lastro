from datetime import date

from sqlmodel.ext.asyncio.session import AsyncSession

from lastro.models.price_history import PriceHistory


async def record_price_point(
    session: AsyncSession, position_id: int, on_date: date, price_cents: int
) -> None:
    """Registra um ponto no histórico de preço da posição. Cada aporte, venda
    ou refresh de cotação tira uma 'foto' do preço naquele momento — o gráfico
    do ativo é construído a partir desses pontos, sem busca retroativa."""
    session.add(PriceHistory(position_id=position_id, date=on_date, price_cents=price_cents))
