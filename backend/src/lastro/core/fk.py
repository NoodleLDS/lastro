from fastapi import HTTPException
from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession


async def ensure_fk_exists(
    session: AsyncSession,
    model: type[SQLModel],
    fk_id: int,
    field_name: str,
) -> None:
    """Garante que a FK referenciada existe antes do insert.

    SQLite não está com PRAGMA foreign_keys=ON neste projeto, então a
    checagem é feita explicitamente aqui para evitar registros órfãos.
    Levanta 422 (entrada inválida do cliente), não 404 (o recurso em si
    existe; a referência que ele aponta é que não existe).
    """
    referenced = await session.get(model, fk_id)
    if referenced is None:
        raise HTTPException(status_code=422, detail=f"{field_name} não encontrado(a)")
