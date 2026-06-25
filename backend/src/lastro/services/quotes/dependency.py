from fastapi import HTTPException

from lastro.core.config import settings
from lastro.models.position import AssetType
from lastro.services.quotes.brapi import BrapiProvider
from lastro.services.quotes.coingecko import CoinGeckoProvider
from lastro.services.quotes.provider import QuoteProvider


def get_quote_provider(asset_type: AssetType) -> QuoteProvider:
    if asset_type == AssetType.CRYPTO:
        return CoinGeckoProvider()

    if not settings.brapi_token:
        raise HTTPException(
            status_code=400,
            detail="cotação B3 requer token brapi, configure LASTRO_BRAPI_TOKEN",
        )
    return BrapiProvider(settings.brapi_token)
