import httpx
import pytest

from lastro.services.quotes.tesouro_direto import TesouroDiretoProvider

_CSV_BODY = (
    "Tipo Titulo;Data Vencimento;Data Base;Taxa Compra Manha;Taxa Venda Manha;"
    "PU Compra Manha;PU Venda Manha;PU Base Manha\r\n"
    "Tesouro IPCA+ com Juros Semestrais;15/05/2035;25/06/2026;7,98;8,10;4200,00;4160,00;4160,00\r\n"
    "Tesouro IPCA+ com Juros Semestrais;15/05/2035;26/06/2026;8,00;8,12;4208,21;4173,93;4173,93\r\n"
    "Tesouro Selic;01/03/2031;26/06/2026;0,05;0,10;15000,00;14999,00;14999,00\r\n"
).encode("latin-1")


def _mock_transport() -> httpx.MockTransport:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, content=_CSV_BODY)

    return httpx.MockTransport(handler)


def _patch_async_client(monkeypatch: pytest.MonkeyPatch) -> None:
    real_async_client = httpx.AsyncClient
    monkeypatch.setattr(
        httpx,
        "AsyncClient",
        lambda *args, **kwargs: real_async_client(*args, transport=_mock_transport(), **kwargs),
    )


async def test_get_quote_retorna_pu_venda_mais_recente(monkeypatch: pytest.MonkeyPatch) -> None:
    _patch_async_client(monkeypatch)

    provider = TesouroDiretoProvider()
    quote = await provider.get_quote("TESOURO_IPCA_2035")

    assert quote.price_cents == 417393


async def test_get_quote_ticker_invalido_retorna_400() -> None:
    provider = TesouroDiretoProvider()

    with pytest.raises(Exception) as exc_info:
        await provider.get_quote("BBAS3")

    assert "400" in str(exc_info.value) or "padrão" in str(exc_info.value)


async def test_get_quote_titulo_nao_encontrado_retorna_502(monkeypatch: pytest.MonkeyPatch) -> None:
    _patch_async_client(monkeypatch)

    provider = TesouroDiretoProvider()

    with pytest.raises(Exception) as exc_info:
        await provider.get_quote("TESOURO_IPCA_2099")

    assert "502" in str(exc_info.value) or "não encontrado" in str(exc_info.value)
