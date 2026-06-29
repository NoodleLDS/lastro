import csv
import io
import re
from datetime import datetime

import httpx
from fastapi import HTTPException

from lastro.services.quotes.provider import Quote

_CSV_URL = (
    "https://www.tesourotransparente.gov.br/ckan/dataset/"
    "df56aa42-484a-4a59-8184-7676580c81e3/resource/"
    "796d2059-14e9-44e3-80c9-2d9e30b405c1/download/PrecoTaxaTesouroDireto.csv"
)


def _parse_brl_number(value: str) -> float:
    return float(value.replace(".", "").replace(",", "."))


def _parse_date(value: str) -> datetime:
    return datetime.strptime(value, "%d/%m/%Y")


class TesouroDiretoProvider:
    async def get_quote(self, ticker: str) -> Quote:
        match = re.match(r"^TESOURO_([A-Z]+)_(\d{4})$", ticker.upper())
        if match is None:
            raise HTTPException(
                status_code=400,
                detail=f"ticker '{ticker}' não segue o padrão TESOURO_<INDEXADOR>_<ANO>",
            )
        indexer, maturity_year = match.group(1), match.group(2)

        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(_CSV_URL)
            response.raise_for_status()
            text = response.content.decode("latin-1")

        rows = csv.DictReader(io.StringIO(text), delimiter=";")
        best_row: dict[str, str] | None = None
        best_date: datetime | None = None
        for row in rows:
            tipo_titulo = row["Tipo Titulo"]
            if indexer.lower() not in tipo_titulo.lower().replace("-", "").replace("+", ""):
                continue
            if not row["Data Vencimento"].endswith(maturity_year):
                continue

            data_base = _parse_date(row["Data Base"])
            if best_date is None or data_base > best_date:
                best_date = data_base
                best_row = row

        if best_row is None:
            raise HTTPException(
                status_code=502,
                detail=f"título do Tesouro Direto não encontrado para '{ticker}'",
            )

        price = _parse_brl_number(best_row["PU Venda Manha"])
        return Quote(ticker=ticker, price_cents=round(price * 100))
