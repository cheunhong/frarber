from typing import Optional

import ccxt.pro as ccxtpro
from ccxt.base.exchange import Exchange
from ccxt.base.types import ConstructorArgs

from frarber.config import load_config
from frarber.constants import ALLOWED_EXCHANGES
from frarber.enums.exchange_type import ExchangeType


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
    if not with_credential:
        return getattr(ccxtpro, exchange.value)()

    options: dict[str, Optional[str]] = {
        "brokerId": None,
        "broker": None,
    }
    if exchange == ExchangeType.BITGET:
        # Bitget cant serialize None broker
        options["broker"] = "a"

    config = load_config()
    exchanges = config.exchanges
    if exchange not in exchanges:
        raise ValueError(f"Exchange {exchange} is not configured.")
    exchange_config = exchanges[exchange]
    if exchange not in ALLOWED_EXCHANGES:
        raise ValueError(f"Exchange {exchange} is not supported.")
    return getattr(ccxtpro, exchange.value)(
        ConstructorArgs(
            apiKey=exchange_config.api_key.get_secret_value(),
            secret=exchange_config.api_secret.get_secret_value(),
            password=(
                exchange_config.password.get_secret_value()
                if exchange_config.password
                else None
            ),
            options=options,
            verbose=verbose,
        ),
    )
