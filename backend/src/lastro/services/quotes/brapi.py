import httpx

from lastro.services.quotes.provider import Quote

_BRAPI_URL = "https://brapi.dev/api/quote/{ticker}"


class BrapiProvider:
    def __init__(self, token: str) -> None:
        self._token = token

    async def get_quote(self, ticker: str) -> Quote:
        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.get(
                _BRAPI_URL.format(ticker=ticker), params={"token": self._token}
            )
            response.raise_for_status()
            body = response.json()

        result = body["results"][0]
        price = result["regularMarketPrice"]
        return Quote(
            ticker=ticker,
            price_cents=round(price * 100),
            price_earnings=result.get("priceEarnings"),
            earnings_per_share=result.get("earningsPerShare"),
        )
