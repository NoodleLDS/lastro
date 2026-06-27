from datetime import date

from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from lastro.models.allocation_target import AllocationTarget
from lastro.models.contribution import Contribution
from lastro.models.dividend import Dividend
from lastro.models.position import Position
from lastro.models.sale import Sale
from lastro.services.analytics.allocation import calculate_allocation
from lastro.services.analytics.magic_number import calculate_magic_number
from lastro.services.analytics.total_return import calculate_total_return
from lastro.services.analytics.valuation import calculate_valuation
from lastro.services.portfolio.average_price import calculate_average_price_cents


def _format_cents(cents: int) -> str:
    return f"R$ {cents / 100:,.2f}".replace(",", "_").replace(".", ",").replace("_", ".")


async def build_portfolio_context(session: AsyncSession) -> str:
    """Monta um snapshot textual do estado vivo da carteira para injetar no
    prompt do analista IA — preço, total return, número mágico e alocação
    real vs meta de cada posição ativa. Sem dado disponível, a posição
    aparece sem aquele campo (a IA não deve inventar)."""
    positions_result = await session.exec(select(Position).where(Position.is_active.is_(True)))
    positions = positions_result.all()

    targets_result = await session.exec(select(AllocationTarget))
    targets = targets_result.all()
    allocation = calculate_allocation(positions, targets)
    allocation_by_type = {item.asset_type: item for item in allocation}

    lines = ["# Carteira atual\n"]

    for position in positions:
        contributions_result = await session.exec(
            select(Contribution).where(Contribution.position_id == position.id)
        )
        contributions = contributions_result.all()
        average_price_cents = calculate_average_price_cents(contributions)

        parts = [
            f"- {position.ticker} ({position.asset_type}): "
            f"{position.quantity} cotas, preço médio {_format_cents(average_price_cents)}"
        ]

        if position.last_price_cents is not None:
            parts.append(f"preço atual {_format_cents(position.last_price_cents)}")

            dividends_result = await session.exec(
                select(Dividend).where(Dividend.position_id == position.id)
            )
            dividends = dividends_result.all()
            sales_result = await session.exec(select(Sale).where(Sale.position_id == position.id))
            sales = sales_result.all()

            total_return = calculate_total_return(
                contributions, dividends, position.last_price_cents, sales
            )
            parts.append(f"total return {total_return.total_return_pct:.2f}%")

            magic_number = calculate_magic_number(
                dividends, position.last_price_cents, date.today()
            )
            if magic_number is not None:
                status = "atingido" if magic_number.is_achieved else "não atingido"
                parts.append(f"número mágico {status}")

            valuation = calculate_valuation(
                dividends, position.target_yield_pct, position.last_price_cents, date.today()
            )
            if valuation is not None:
                veredito = "subvalorizado" if valuation.is_undervalued else "sobrevalorizado"
                parts.append(
                    f"preço-teto (DY-alvo {position.target_yield_pct:.1f}%) "
                    f"{_format_cents(valuation.price_ceiling_cents)}, "
                    f"margem de segurança {valuation.margin_of_safety_pct:.1f}% ({veredito})"
                )

        if position.roe_percentage is not None:
            parts.append(f"ROE {position.roe_percentage:.1f}%")
        if position.price_earnings is not None:
            parts.append(f"P/L {position.price_earnings:.1f}")

        lines.append(", ".join(parts))

    lines.append("\n# Alocação por classe (real vs meta)\n")
    for item in allocation_by_type.values():
        target_text = (
            f"meta {item.target_percentage:.1f}%"
            if item.target_percentage is not None
            else "sem meta definida"
        )
        lines.append(f"- {item.asset_type}: real {item.current_percentage:.1f}%, {target_text}")

    return "\n".join(lines)
