import asyncio

from typer import Typer

from frarber.arbitrage import create_arbitrage_order
from frarber.calculate import calculate_unit_size
from frarber.enums.action import Action
from frarber.enums.exchange_type import ExchangeType
from frarber.enums.threshold_direction import ThresholdDirection
from frarber.equity_alert import monitor_equity_threshold
from frarber.exchange import create_exchange
from frarber.price_diff import stream_price_diff
from frarber.utils.symbol import derive_symbol

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
    long_symbol = derive_symbol(long_exchange_type, symbol)
    short_symbol = derive_symbol(short_exchange_type, symbol)

    asyncio.run(
        create_arbitrage_order(
            action=Action.OPEN,
            long_exchange=long_exchange,
            short_exchange=short_exchange,
            long_symbol=long_symbol,
            short_symbol=short_symbol,
            total_size=total_size,
            timeout=timeout,
            threshold=threshold,
        )
    )

    async def close_exchanges():
        await asyncio.gather(long_exchange.close(), short_exchange.close())

    asyncio.run(close_exchanges())


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
            long_symbol=derive_symbol(long_exchange_type, symbol),
            short_symbol=derive_symbol(short_exchange_type, symbol),
            total_size=total_size,
            timeout=timeout,
            threshold=threshold,
        )
    )

    async def close_exchanges():
        await asyncio.gather(long_exchange.close(), short_exchange.close())

    asyncio.run(close_exchanges())


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

    buy_exchange = create_exchange(buy_exchange_type, with_credential=False)
    sell_exchange = create_exchange(sell_exchange_type, with_credential=False)

    async def main():
        async for _ in stream_price_diff(
            buy_exchange=buy_exchange,
            sell_exchange=sell_exchange,
            buy_symbol=derive_symbol(buy_exchange_type, symbol),
            sell_symbol=derive_symbol(sell_exchange_type, symbol),
            update_interval=update_interval,
            log_updates=log_updates,
        ):
            pass
        await asyncio.gather(buy_exchange.close(), sell_exchange.close())

    asyncio.run(main())


@app.command()
def unit_size(
    exchange_type: ExchangeType,
    symbol: str,
    target_amount: float,
):
    """
    Calculate the maximum unit size that can be bought with the target amount on the given exchange.

    :param exchange: The exchange to use for the calculation.
    :param symbol: The trading pair symbol (e.g., 'BTC/USD').
    :param target_amount: The amount of quote currency to spend (e.g., USD).
    """

    exchange = create_exchange(exchange_type, with_credential=False)
    symbol = derive_symbol(exchange_type, symbol)

    async def main():
        unit_size = await calculate_unit_size(
            exchange=exchange,
            symbol=symbol,
            target_amount=target_amount,
        )
        print(f"Maximum unit size that can be bought: {unit_size}")
        await exchange.close()

    asyncio.run(main())


@app.command()
def equity_alert(
    exchange_type: ExchangeType,
    webhook_url: str,
    threshold: float,
    direction: ThresholdDirection = ThresholdDirection.BELOW,
    currency: str = "USDT",
    check_interval: float = 10.0,
    balance_type: str | None = None,
    trigger_once: bool = True,
):
    """Send a webhook alert when the futures account equity crosses the threshold."""

    exchange = create_exchange(exchange_type)

    async def main() -> None:
        try:
            await monitor_equity_threshold(
                exchange=exchange,
                exchange_type=exchange_type,
                threshold=threshold,
                direction=direction,
                webhook_url=webhook_url,
                currency=currency,
                check_interval=check_interval,
                trigger_once=trigger_once,
                balance_type=balance_type,
            )
        finally:
            await exchange.close()  # type: ignore[attr-defined]

    asyncio.run(main())


if __name__ == "__main__":
    app()
