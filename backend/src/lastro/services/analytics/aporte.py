from pydantic import BaseModel
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from lastro.models.allocation_target import AllocationTarget
from lastro.models.contribution import Contribution
from lastro.models.position import AssetType, Position
from lastro.services.analytics.allocation import calculate_allocation

CPTS_PRIORITY_PCT = 0.25
CPTS_TICKER = "CPTS11"
BBAS3_MIN_ROE_PCT = 15.0
ROTATING_TICKERS = ("XPML11", "HGLG11")

# Excluídos do motor de aporte mensal, conforme master prompt:
# Tesouro (cupom semestral interrompe o composto), PSEC/BTCI/BOVA/TAEE (em saída),
# BTC (satélite, fora do aporte regular), IVVB11 (só recebe capital extraordinário).
_EXCLUDED_TICKERS = frozenset(
    {"TESOURO_IPCA_2035", "PSEC11", "BTCI11", "BOVA11", "TAEE4", "BTC", "IVVB11"}
)

# Sem prioridade: só recebem se a classe estiver desviada e não houver candidato melhor.
_LOW_PRIORITY_TICKERS = frozenset({"PETR4", "CMIG4"})

BBAS3_TICKER = "BBAS3"


class ContributionAllocation(BaseModel):
    ticker: str
    amount_cents: int
    reason: str


class ContributionPreview(BaseModel):
    total_cents: int
    allocations: list[ContributionAllocation]


def _is_bbas3_eligible(position: Position) -> bool:
    return position.roe_percentage is not None and position.roe_percentage >= BBAS3_MIN_ROE_PCT


async def _last_rotation_winner(
    session: AsyncSession, positions_by_ticker: dict[str, Position]
) -> str | None:
    rotating_ids = [
        positions_by_ticker[ticker].id
        for ticker in ROTATING_TICKERS
        if ticker in positions_by_ticker
    ]
    if not rotating_ids:
        return None

    statement = (
        select(Contribution)
        .where(Contribution.position_id.in_(rotating_ids))
        .order_by(Contribution.date.desc(), Contribution.id.desc())
    )
    result = await session.exec(statement)
    last = result.first()
    if last is None:
        return None

    for ticker in ROTATING_TICKERS:
        position = positions_by_ticker.get(ticker)
        if position is not None and position.id == last.position_id:
            other_ticker = next(t for t in ROTATING_TICKERS if t != ticker)
            return other_ticker if other_ticker in positions_by_ticker else ticker
    return None


def _eligible_tickers(
    positions_by_ticker: dict[str, Position], rotation_winner: str | None
) -> list[str]:
    eligible: list[str] = []
    for ticker, position in positions_by_ticker.items():
        if ticker == CPTS_TICKER:
            continue
        if ticker in _EXCLUDED_TICKERS:
            continue
        if ticker in ROTATING_TICKERS and ticker != rotation_winner:
            continue
        if ticker == BBAS3_TICKER and not _is_bbas3_eligible(position):
            continue
        eligible.append(ticker)
    return eligible


def _pick_target_ticker(
    eligible_tickers: list[str],
    positions_by_ticker: dict[str, Position],
    deviation_by_type: dict[AssetType, float],
) -> str | None:
    if not eligible_tickers:
        return None

    def sort_key(ticker: str) -> tuple[int, float]:
        position = positions_by_ticker[ticker]
        low_priority = 1 if ticker in _LOW_PRIORITY_TICKERS else 0
        deviation = deviation_by_type.get(position.asset_type, 0.0)
        return (low_priority, deviation)

    return min(eligible_tickers, key=sort_key)


async def distribute_contribution(session: AsyncSession, total_cents: int) -> ContributionPreview:
    """Distribui um aporte novo entre os ativos elegíveis, sem vender nada,
    aproximando a carteira da AllocationTarget. CPTS recebe uma fatia
    prioritária fixa; o restante segue rotação XPML/HGLG e desvio de classe."""
    positions_result = await session.exec(select(Position).where(Position.is_active.is_(True)))
    positions = positions_result.all()
    positions_by_ticker = {position.ticker: position for position in positions}

    targets_result = await session.exec(select(AllocationTarget))
    targets = targets_result.all()

    allocations: list[ContributionAllocation] = []
    remaining_cents = total_cents

    if CPTS_TICKER in positions_by_ticker:
        cpts_cents = round(total_cents * CPTS_PRIORITY_PCT)
        allocations.append(
            ContributionAllocation(
                ticker=CPTS_TICKER,
                amount_cents=cpts_cents,
                reason="prioridade fixa (motor de acumulação)",
            )
        )
        remaining_cents -= cpts_cents

    rotation_winner = await _last_rotation_winner(session, positions_by_ticker)
    if rotation_winner is None and any(t in positions_by_ticker for t in ROTATING_TICKERS):
        rotation_winner = ROTATING_TICKERS[0]

    eligible_tickers = _eligible_tickers(positions_by_ticker, rotation_winner)

    if remaining_cents > 0 and eligible_tickers:
        breakdown = calculate_allocation(positions, targets)
        deviation_by_type = {
            item.asset_type: item.deviation_pct
            for item in breakdown
            if item.deviation_pct is not None
        }

        target_ticker = _pick_target_ticker(
            eligible_tickers, positions_by_ticker, deviation_by_type
        )
        if target_ticker is not None:
            reason = (
                "rotação XPML/HGLG + classe sub-alocada"
                if target_ticker in ROTATING_TICKERS
                else "classe mais sub-alocada"
            )
            allocations.append(
                ContributionAllocation(
                    ticker=target_ticker, amount_cents=remaining_cents, reason=reason
                )
            )

    return ContributionPreview(total_cents=total_cents, allocations=allocations)
