from datetime import date

from lastro.models.dividend import Dividend
from lastro.services.analytics.magic_number import calculate_magic_number


def _dividend(year: int, month: int, amount_cents: int) -> Dividend:
    return Dividend(position_id=1, date=date(year, month, 1), amount_cents=amount_cents)


def test_numero_magico_atingido_quando_dividendo_compra_uma_cota_ou_mais() -> None:
    # 12 meses de R$10 = R$120 total / 12 = R$10/mês médio, preço R$10 -> 1.0 cota/mês
    dividends = [_dividend(2025, m, 1000) for m in range(7, 13)] + [
        _dividend(2026, m, 1000) for m in range(1, 7)
    ]

    result = calculate_magic_number(dividends, current_price_cents=1000, today=date(2026, 6, 25))

    assert result is not None
    assert result.average_monthly_dividend_cents == 1000
    assert result.shares_bought_per_month == 1.0
    assert result.is_achieved is True


def test_numero_magico_nao_atingido_quando_dividendo_compra_menos_de_uma_cota() -> None:
    dividends = [_dividend(2026, m, 500) for m in range(1, 7)]

    result = calculate_magic_number(dividends, current_price_cents=1000, today=date(2026, 6, 25))

    assert result is not None
    assert result.shares_bought_per_month == 0.5
    assert result.is_achieved is False


def test_numero_magico_usa_media_dos_meses_com_dado_quando_historico_curto() -> None:
    # só 3 meses de histórico: média deve ser sobre 3, não sobre 12
    dividends = [_dividend(2026, m, 900) for m in (4, 5, 6)]

    result = calculate_magic_number(dividends, current_price_cents=900, today=date(2026, 6, 25))

    assert result is not None
    assert result.average_monthly_dividend_cents == 900
    assert result.shares_bought_per_month == 1.0


def test_numero_magico_ignora_dividendos_fora_da_janela_de_12_meses() -> None:
    old = _dividend(2024, 1, 100_000)
    recent = [_dividend(2026, m, 1000) for m in range(1, 7)]

    result = calculate_magic_number(
        [old, *recent], current_price_cents=1000, today=date(2026, 6, 25)
    )

    assert result is not None
    assert result.average_monthly_dividend_cents == 1000


def test_numero_magico_none_sem_dividendo_no_periodo() -> None:
    result = calculate_magic_number([], current_price_cents=1000, today=date(2026, 6, 25))

    assert result is None


def test_numero_magico_none_sem_preco_atual() -> None:
    dividends = [_dividend(2026, 6, 1000)]

    result = calculate_magic_number(dividends, current_price_cents=0, today=date(2026, 6, 25))

    assert result is None
