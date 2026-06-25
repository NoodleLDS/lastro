import httpx

from lastro.services.quotes.provider import Quote

_COINGECKO_URL = "https://api.coingecko.com/api/v3/simple/price"

_TICKER_TO_COINGECKO_ID = {
    "BTC": "bitcoin",
    "ETH": "ethereum",
}


class CoinGeckoProvider:
    async def get_quote(self, ticker: str) -> Quote:
        coin_id = _TICKER_TO_COINGECKO_ID.get(ticker.upper(), ticker.lower())

        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.get(
                _COINGECKO_URL, params={"ids": coin_id, "vs_currencies": "brl"}
            )
            response.raise_for_status()
            body = response.json()

        price = body[coin_id]["brl"]
        return Quote(ticker=ticker, price_cents=round(price * 100))
