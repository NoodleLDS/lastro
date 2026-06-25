from sqlmodel.ext.asyncio.session import AsyncSession

from lastro.models.position import Position


async def apply_quantity_delta(session: AsyncSession, position_id: int, delta: float) -> None:
    """Soma (compra, delta positivo) ou subtrai (venda, delta negativo) da
    quantidade da posição. Position.quantity é a fonte da verdade do que o
    usuário possui hoje; Contribution/Sale são o extrato de como chegou lá."""
    position = await session.get(Position, position_id)
    if position is None:
        return
    position.quantity += delta
    session.add(position)
