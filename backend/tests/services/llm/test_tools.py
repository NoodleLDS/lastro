from sqlmodel.ext.asyncio.session import AsyncSession

from lastro.models.emergency_reserve import EmergencyReserve
from lastro.models.income import Income
from lastro.services.llm.tools import execute_tool


async def test_execute_tool_desconhecida_retorna_mensagem_de_erro(session: AsyncSession) -> None:
    result = await execute_tool(session, "tool_que_nao_existe", {})

    assert "Ferramenta desconhecida" in result


async def test_execute_tool_get_emergency_reserve_sem_dados(session: AsyncSession) -> None:
    result = await execute_tool(session, "get_emergency_reserve", {})

    assert "Nenhuma reserva" in result


async def test_execute_tool_get_emergency_reserve_com_dados(session: AsyncSession) -> None:
    session.add(EmergencyReserve(institution="Nubank", balance_cents=1_200_000, cdi_percentage=102))
    await session.commit()

    result = await execute_tool(session, "get_emergency_reserve", {})

    assert "Nubank" in result
    assert "12.000,00" in result
    assert "102%" in result


async def test_execute_tool_get_monthly_summary(session: AsyncSession) -> None:
    session.add(Income(year=2026, month=6, description="Salário", amount_cents=690_000))
    await session.commit()

    result = await execute_tool(session, "get_monthly_summary", {"year": 2026, "month": 6})

    assert "06/2026" in result
    assert "6.900,00" in result


async def test_execute_tool_get_transactions_sem_resultados(session: AsyncSession) -> None:
    result = await execute_tool(
        session, "get_transactions", {"year": 2026, "month": 6, "search": "inexistente"}
    )

    assert "Nenhuma transação" in result


async def test_execute_tool_com_argumento_obrigatorio_faltando_retorna_erro(
    session: AsyncSession,
) -> None:
    result = await execute_tool(session, "get_monthly_summary", {"year": 2026})

    assert "Erro ao executar get_monthly_summary" in result
