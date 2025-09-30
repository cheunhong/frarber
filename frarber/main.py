import asyncio

from typer import Typer

from frarber.arbitrage import create_arbitrage_order
from frarber.enums.action import Action
from frarber.enums.exchange_type import ExchangeType
from frarber.exchange import create_exchange
from frarber.price_diff import stream_price_diff

app = Typer()


@app.command()
def open(
    long_exchange_type: ExchangeType,
    short_exchange_type: ExchangeType,
    symbol: str,
    total_size: float,
    timeout: int = 1800,
    threshold: float = 0.001,
):
    """
    Open an arbitrage position between two exchanges.

    :param long_exchange: The exchange to go long on.
    :param short_exchange: The exchange to go short on.
    :param symbol: The trading pair symbol.
    :param total_size: The total size of the arbitrage order.
    :param timeout: The maximum time to wait for the arbitrage to complete (in seconds).
    :param threshold: The price difference threshold for arbitrage opportunity (as a decimal).
    """

    long_exchange = create_exchange(long_exchange_type)
    short_exchange = create_exchange(short_exchange_type)

    asyncio.run(
        create_arbitrage_order(
            action=Action.OPEN,
            long_exchange=long_exchange,
            short_exchange=short_exchange,
            symbol=symbol,
            total_size=total_size,
            timeout=timeout,
            threshold=threshold,
        )
    )


@app.command()
def close(
    long_exchange_type: ExchangeType,
    short_exchange_type: ExchangeType,
    symbol: str,
    total_size: float,
    timeout: int = 1800,
    threshold: float = 0.001,
):
    """
    Close an arbitrage position between two exchanges.

    :param long_exchange: The exchange to close the long position on.
    :param short_exchange: The exchange to close the short position on.
    :param symbol: The trading pair symbol.
    :param total_size: The total size of the arbitrage order.
    :param timeout: The maximum time to wait for the arbitrage to complete (in seconds).
    :param threshold: The price difference threshold for arbitrage opportunity (as a decimal).
    """

    long_exchange = create_exchange(long_exchange_type)
    short_exchange = create_exchange(short_exchange_type)

    asyncio.run(
        create_arbitrage_order(
            action=Action.CLOSE,
            long_exchange=long_exchange,
            short_exchange=short_exchange,
            symbol=symbol,
            total_size=total_size,
            timeout=timeout,
            threshold=threshold,
        )
    )


@app.command()
def price_diff(
    buy_exchange_type: ExchangeType,
    sell_exchange_type: ExchangeType,
    symbol: str,
    update_interval: float = 1.0,
    log_updates: bool = True,
):
    """
    Stream the price difference between the top ask of buy_exchange and top bid of sell_exchange.

    :param buy_exchange: Exchange to go long on (we monitor the ask price)
    :param sell_exchange: Exchange to go short on (we monitor the bid price)
    :param symbol: Trading pair symbol
    :param update_interval: Time between price updates in seconds
    :param log_updates: Whether to log price updates
    """

    buy_exchange = create_exchange(buy_exchange_type)
    sell_exchange = create_exchange(sell_exchange_type)

    async def main():
        async for _ in stream_price_diff(
            buy_exchange=buy_exchange,
            sell_exchange=sell_exchange,
            symbol=symbol,
            update_interval=update_interval,
            log_updates=log_updates,
        ):
            pass

    asyncio.run(main())
