import pytest
from fastapi import HTTPException

from lastro.core.config import settings
from lastro.models.position import AssetType
from lastro.services.quotes.brapi import BrapiProvider
from lastro.services.quotes.coingecko import CoinGeckoProvider
from lastro.services.quotes.dependency import get_quote_provider


def test_crypto_retorna_coingecko_sem_precisar_de_token() -> None:
    provider = get_quote_provider(AssetType.CRYPTO)

    assert isinstance(provider, CoinGeckoProvider)


def test_stock_sem_token_configurado_levanta_400() -> None:
    original = settings.brapi_token
    settings.brapi_token = None
    try:
        with pytest.raises(HTTPException) as exc_info:
            get_quote_provider(AssetType.STOCK)
        assert exc_info.value.status_code == 400
    finally:
        settings.brapi_token = original


def test_stock_com_token_configurado_retorna_brapi() -> None:
    original = settings.brapi_token
    settings.brapi_token = "fake-token"
    try:
        provider = get_quote_provider(AssetType.STOCK)
        assert isinstance(provider, BrapiProvider)
    finally:
        settings.brapi_token = original
