from datetime import date

import httpx

_BCB_SGS_LATEST_URL = (
    "https://api.bcb.gov.br/dados/serie/bcdata.sgs.{code}/dados/ultimos/1?formato=json"
)
_BCB_SGS_RANGE_URL = (
    "https://api.bcb.gov.br/dados/serie/bcdata.sgs.{code}/dados"
    "?formato=json&dataInicial={start}&dataFinal={end}"
)

_CDI_SERIES_CODE = 12
_IPCA_SERIES_CODE = 433


class BCBProvider:
    """Busca séries do SGS do Banco Central (ex.: CDI diário, IPCA mensal).
    Não implementa QuoteProvider: não é cotação de ticker, é taxa de
    referência pública, sem necessidade de token."""

    async def get_cdi_rate(self) -> float:
        return await self._get_latest_rate(_CDI_SERIES_CODE)

    async def get_ipca_rate(self) -> float:
        return await self._get_latest_rate(_IPCA_SERIES_CODE)

    async def get_accumulated_rate(self, series_code: int, start: date, end: date) -> float:
        """Soma as taxas (percentuais) da série entre `start` e `end`,
        aproximando a taxa acumulada do período (CDI/IPCA mensal somado)."""
        url = _BCB_SGS_RANGE_URL.format(
            code=series_code,
            start=start.strftime("%d/%m/%Y"),
            end=end.strftime("%d/%m/%Y"),
        )
        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.get(url)
            response.raise_for_status()
            body = response.json()

        return sum(float(item["valor"]) for item in body)

    async def _get_latest_rate(self, series_code: int) -> float:
        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.get(_BCB_SGS_LATEST_URL.format(code=series_code))
            response.raise_for_status()
            body = response.json()

        return float(body[0]["valor"])
