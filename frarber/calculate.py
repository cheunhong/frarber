from ccxt.base.exchange import Exchange


async def calculate_unit_size(
    exchange: Exchange,
    symbol: str,
    target_amount: float,
):
    """
    Calculate the maximum unit size that can be bought with the target amount on the given exchange.

    :param exchange: The exchange to use for the calculation.
    :param symbol: The trading pair symbol (e.g., 'BTC/USD').
    :param target_amount: The amount of quote currency to spend (e.g., USD).
    :return: The maximum unit size that can be bought.
    """
    ticker = await exchange.fetch_ticker(symbol)
    last_price = ticker["last"]
    return target_amount / last_price
