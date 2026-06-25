import pytest

from lastro.services.ingest.quick_entry import QuickEntryParseError, parse_quick_entry


def test_descricao_simples_sem_categoria_sem_parcela() -> None:
    entry = parse_quick_entry("zebu 22")

    assert entry.description == "zebu"
    assert entry.amount_cents == 2200
    assert entry.category_name is None
    assert entry.installment_current is None
    assert entry.installment_total is None


def test_com_categoria() -> None:
    entry = parse_quick_entry("posto 35 #transporte")

    assert entry.description == "posto"
    assert entry.amount_cents == 3500
    assert entry.category_name == "transporte"


def test_com_parcela_e_decimal_com_virgula() -> None:
    entry = parse_quick_entry("tablet 335,98 3/9")

    assert entry.description == "tablet"
    assert entry.amount_cents == 33598
    assert entry.installment_current == 3
    assert entry.installment_total == 9


def test_descricao_com_multiplas_palavras() -> None:
    entry = parse_quick_entry("posto de gasolina 100")

    assert entry.description == "posto de gasolina"
    assert entry.amount_cents == 10000


def test_decimal_com_um_digito() -> None:
    entry = parse_quick_entry("zebu 22,5")

    assert entry.amount_cents == 2250


def test_decimal_com_ponto() -> None:
    entry = parse_quick_entry("zebu 22.50")

    assert entry.amount_cents == 2250


def test_espacos_extras_multiplos() -> None:
    entry = parse_quick_entry("zebu   22   #transporte   3/9")

    assert entry.description == "zebu"
    assert entry.amount_cents == 2200
    assert entry.category_name == "transporte"
    assert entry.installment_current == 3
    assert entry.installment_total == 9


def test_categoria_antes_da_parcela_e_parcela_antes_da_categoria() -> None:
    com_categoria_primeiro = parse_quick_entry("zebu 22 #transporte 3/9")
    com_parcela_primeiro = parse_quick_entry("zebu 22 3/9 #transporte")

    assert com_categoria_primeiro.category_name == "transporte"
    assert com_categoria_primeiro.installment_current == 3
    assert com_parcela_primeiro.category_name == "transporte"
    assert com_parcela_primeiro.installment_current == 3


def test_erro_sem_valor() -> None:
    with pytest.raises(QuickEntryParseError):
        parse_quick_entry("zebu")


def test_erro_valor_nao_numerico() -> None:
    with pytest.raises(QuickEntryParseError):
        parse_quick_entry("zebu abc")


def test_erro_parcela_com_hifen() -> None:
    with pytest.raises(QuickEntryParseError):
        parse_quick_entry("zebu 22 3-9")


def test_erro_ordem_invertida_parcela_antes_do_valor() -> None:
    with pytest.raises(QuickEntryParseError):
        parse_quick_entry("tablet 3/9 335,98")


def test_erro_valor_zero() -> None:
    with pytest.raises(QuickEntryParseError):
        parse_quick_entry("zebu 0")


def test_erro_valor_negativo() -> None:
    with pytest.raises(QuickEntryParseError):
        parse_quick_entry("zebu -22")


def test_erro_parcela_atual_maior_que_total() -> None:
    with pytest.raises(QuickEntryParseError):
        parse_quick_entry("zebu 22 9/3")


def test_erro_categoria_vazia() -> None:
    with pytest.raises(QuickEntryParseError):
        parse_quick_entry("zebu 22 #")


def test_erro_entrada_vazia() -> None:
    with pytest.raises(QuickEntryParseError):
        parse_quick_entry("   ")


def test_descricao_com_numero_no_meio_nao_confunde_valor() -> None:
    entry = parse_quick_entry("hotel 5 estrelas 200")

    assert entry.description == "hotel 5 estrelas"
    assert entry.amount_cents == 20000


def test_erro_categoria_duplicada() -> None:
    with pytest.raises(QuickEntryParseError):
        parse_quick_entry("zebu 22 #transporte #lazer")


def test_erro_parcela_duplicada() -> None:
    with pytest.raises(QuickEntryParseError):
        parse_quick_entry("zebu 22 3/9 4/9")
