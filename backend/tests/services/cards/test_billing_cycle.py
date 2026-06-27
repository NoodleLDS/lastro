from datetime import date, timedelta

from lastro.services.cards.billing_cycle import billing_cycle_range


def test_picpay_fatura_de_junho_cobre_8_maio_a_7_junho() -> None:
    date_from, date_to = billing_cycle_range(closing_day=7, reference_year=2026, reference_month=6)

    assert date_from == date(2026, 5, 8)
    assert date_to == date(2026, 6, 7)


def test_inter_fatura_de_junho_cobre_9_maio_a_8_junho() -> None:
    date_from, date_to = billing_cycle_range(closing_day=8, reference_year=2026, reference_month=6)

    assert date_from == date(2026, 5, 9)
    assert date_to == date(2026, 6, 8)


def test_santander_fatura_de_junho_cobre_4_maio_a_3_junho() -> None:
    date_from, date_to = billing_cycle_range(closing_day=3, reference_year=2026, reference_month=6)

    assert date_from == date(2026, 5, 4)
    assert date_to == date(2026, 6, 3)


def test_closing_day_em_mes_curto_usa_ultimo_dia_disponivel() -> None:
    date_from, date_to = billing_cycle_range(closing_day=31, reference_year=2026, reference_month=3)

    assert date_from == date(2026, 2, 28) + timedelta(days=1)
    assert date_to == date(2026, 3, 31)


def test_virada_de_ano() -> None:
    date_from, date_to = billing_cycle_range(closing_day=7, reference_year=2026, reference_month=1)

    assert date_from == date(2025, 12, 8)
    assert date_to == date(2026, 1, 7)
