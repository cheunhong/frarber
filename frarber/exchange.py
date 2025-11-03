from ccxt.base.exchange import Exchange
from ccxt.base.types import ConstructorArgs

from frarber.config import load_config
from frarber.enums.exchange_type import ExchangeType
from frarber.exchanges import (
    Binance,
    BinanceCoinM,
    BinanceUSDM,
    Bitget,
    Bybit,
    Mexc,
    Phemex,
)


def create_exchange(
    exchange: ExchangeType,
    with_credential: bool = True,
    verbose: bool = False,
) -> Exchange:
    """
    Create an instance of the specified exchange.

    :param exchange: The exchange to create an instance for.
    :param config: Optional configuration parameters for the exchange.
    :return: An instance of the specified exchange.
    """
    match exchange:
        case ExchangeType.BINANCE:
            exchange_cls = Binance
        case ExchangeType.BINANCE_COINM:
            exchange_cls = BinanceCoinM
        case ExchangeType.BINANCE_USDM:
            exchange_cls = BinanceUSDM
        case ExchangeType.BITGET:
            exchange_cls = Bitget
        case ExchangeType.BYBIT:
            exchange_cls = Bybit
        case ExchangeType.MEXC:
            exchange_cls = Mexc
        case ExchangeType.PHEMEX:
            exchange_cls = Phemex
        case ExchangeType.MEXC_USDTM:
            exchange_cls = Mexc
            exchange = ExchangeType.MEXC
        case _:
            raise ValueError(f"Exchange {exchange} is not supported.")

    if not with_credential:
        return exchange_cls()

    config = load_config()
    exchanges = config.exchanges
    exchange_config = exchanges[exchange]
    return exchange_cls(
        ConstructorArgs(
            apiKey=exchange_config.api_key.get_secret_value(),
            secret=exchange_config.api_secret.get_secret_value(),
            password=(
                exchange_config.password.get_secret_value()
                if exchange_config.password
                else None
            ),
            userToken=(
                exchange_config.user_token.get_secret_value()
                if exchange_config.user_token
                else None
            ),
            httpProxy=config.http_proxy,
            verbose=verbose,
        ),
    )
