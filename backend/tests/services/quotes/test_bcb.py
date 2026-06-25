from datetime import date

import httpx
import pytest

from lastro.services.quotes.bcb import BCBProvider


async def test_get_cdi_rate_parseia_resposta_do_sgs(monkeypatch: pytest.MonkeyPatch) -> None:
    async def fake_get(self: httpx.AsyncClient, url: str, **kwargs: object) -> httpx.Response:
        return httpx.Response(
            status_code=200,
            json=[{"data": "24/06/2026", "valor": "0.04"}],
            request=httpx.Request("GET", url),
        )

    monkeypatch.setattr(httpx.AsyncClient, "get", fake_get)

    provider = BCBProvider()
    rate = await provider.get_cdi_rate()

    assert rate == pytest.approx(0.04)


async def test_get_ipca_rate_parseia_resposta_do_sgs(monkeypatch: pytest.MonkeyPatch) -> None:
    async def fake_get(self: httpx.AsyncClient, url: str, **kwargs: object) -> httpx.Response:
        return httpx.Response(
            status_code=200,
            json=[{"data": "01/06/2026", "valor": "0.35"}],
            request=httpx.Request("GET", url),
        )

    monkeypatch.setattr(httpx.AsyncClient, "get", fake_get)

    provider = BCBProvider()
    rate = await provider.get_ipca_rate()

    assert rate == pytest.approx(0.35)


async def test_get_accumulated_rate_soma_as_taxas_do_periodo(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def fake_get(self: httpx.AsyncClient, url: str, **kwargs: object) -> httpx.Response:
        return httpx.Response(
            status_code=200,
            json=[
                {"data": "01/01/2026", "valor": "0.8"},
                {"data": "01/02/2026", "valor": "0.7"},
                {"data": "01/03/2026", "valor": "0.9"},
            ],
            request=httpx.Request("GET", url),
        )

    monkeypatch.setattr(httpx.AsyncClient, "get", fake_get)

    provider = BCBProvider()
    accumulated = await provider.get_accumulated_rate(
        series_code=12, start=date(2026, 1, 1), end=date(2026, 3, 31)
    )

    assert accumulated == pytest.approx(2.4)
