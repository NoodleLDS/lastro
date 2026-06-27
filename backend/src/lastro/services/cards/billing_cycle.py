from calendar import monthrange
from datetime import date, timedelta


def _clamp_day(year: int, month: int, day: int) -> date:
    last_day = monthrange(year, month)[1]
    return date(year, month, min(day, last_day))


def _add_months(year: int, month: int, delta: int) -> tuple[int, int]:
    total = (year * 12 + (month - 1)) + delta
    return total // 12, total % 12 + 1


def billing_cycle_range(
    closing_day: int, reference_year: int, reference_month: int
) -> tuple[date, date]:
    """Janela de gastos da fatura cujo vencimento cai no mês de referência.

    Ex.: PicPay fecha dia 7, vence dia 15. Fatura que vence em junho cobre
    gastos de 8/maio a 7/junho (mês de referência = mês do vencimento).
    """
    closing_this_cycle = _clamp_day(reference_year, reference_month, closing_day)
    prev_year, prev_month = _add_months(reference_year, reference_month, -1)
    closing_previous_cycle = _clamp_day(prev_year, prev_month, closing_day)

    return closing_previous_cycle + timedelta(days=1), closing_this_cycle
