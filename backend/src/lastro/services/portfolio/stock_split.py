from dataclasses import dataclass
from datetime import date
from typing import Protocol

from lastro.models.stock_split import StockSplit


class _QuantityPriceEvent(Protocol):
    date: date
    quantity: float
    unit_price_cents: int


@dataclass(frozen=True)
class AdjustedEvent:
    """Cópia ajustada de uma Contribution/Sale após aplicar splits — o
    registro original no banco nunca é alterado, só a leitura."""

    date: date
    quantity: float
    unit_price_cents: float


def adjust_for_splits(
    events: list[_QuantityPriceEvent], splits: list[StockSplit]
) -> list[AdjustedEvent]:
    """Ajusta quantidade/preço de eventos anteriores a cada split pelo fator
    ratio_to/ratio_from, preservando o valor total investido. Splits são
    aplicados em ordem cronológica: um evento anterior a dois splits recebe
    os dois fatores compostos."""
    adjusted = [AdjustedEvent(e.date, e.quantity, e.unit_price_cents) for e in events]

    for split in sorted(splits, key=lambda s: s.date):
        factor = split.ratio_to / split.ratio_from
        adjusted = [
            AdjustedEvent(e.date, e.quantity * factor, e.unit_price_cents / factor)
            if e.date < split.date
            else e
            for e in adjusted
        ]

    return adjusted
