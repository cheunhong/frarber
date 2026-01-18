import asyncio
import time

from ccxt.base.errors import InvalidOrder
from ccxt.base.exchange import Exchange
from loguru import logger

from frarber.config import load_config
from frarber.enums.action import Action
from frarber.enums.exchange_type import ExchangeType
from frarber.enums.position_side import PositionSide

from .price_diff import stream_price_diff

DEFAULT_TIMEOUT = 1800  # 30 minutes
DEFAULT_THRESHOLD = 0.0  # 0.0% price difference threshold


def derive_hedged_mode_order_params(
    exchange: ExchangeType,
    action: Action,
    position_side: PositionSide,
) -> dict[str, str] | dict[str, int] | dict[str, bool]:
    match exchange:
        case ExchangeType.BINANCE_USDM:
            return {"positionSide": position_side.value}
        case ExchangeType.BYBIT:
            return {"positionIdx": 1 if position_side == PositionSide.LONG else 2}
        case ExchangeType.BITGET:
            if action == Action.OPEN:
                return {"hedged": True}
            return {"hedged": True, "reduceOnly": True}
        case ExchangeType.PHEMEX:
            return {"posSide": position_side.value.capitalize()}
        case _:
            raise ValueError(f"Unsupported exchange: {exchange}")


async def create_arbitrage_order(
    action: Action,
    long_exchange: Exchange,
    short_exchange: Exchange,
    long_symbol: str,
    short_symbol: str,
    total_size: float,
    timeout: int = DEFAULT_TIMEOUT,
    threshold: float = DEFAULT_THRESHOLD,
):
    """
    Create an arbitrage order between two exchanges using price difference streaming.

    :param action: The action to perform (open or close).
    :param long_exchange: The exchange to go long on.
    :param short_exchange: The exchange to go short on.
    :param symbol: The trading pair symbol.
    :param total_size: The total size of the arbitrage order.
    :param order_size: The size of each individual order.
    :param threshold: The price difference threshold for arbitrage opportunity.
    :param timeout: The maximum time to wait for the arbitrage to complete.
    """
    start_time = time.time()

    config = load_config()
    exchanges = config.exchanges
    long_exchange_type = ExchangeType(long_exchange.__class__.__name__.lower())
    short_exchange_type = ExchangeType(short_exchange.__class__.__name__.lower())
    symbol = long_symbol.split("/")[0]
    if long_exchange_type not in exchanges:
        raise ValueError(f"Exchange {long_exchange.__class__.__name__} not configured.")
    if short_exchange_type not in exchanges:
        raise ValueError(
            f"Exchange {short_exchange.__class__.__name__} not configured."
        )
    long_exchange_config = exchanges[long_exchange_type]
    short_exchange_config = exchanges[short_exchange_type]
    long_params = {}
    short_params = {}
    if long_exchange_config.hedged_mode:
        long_params = derive_hedged_mode_order_params(
            exchange=long_exchange_type,
            action=action,
            position_side=PositionSide.LONG,
        )
    else:
        if action == Action.CLOSE:
            long_params["reduceOnly"] = True
    if short_exchange_config.hedged_mode:
        short_params = derive_hedged_mode_order_params(
            exchange=short_exchange_type,
            action=action,
            position_side=PositionSide.SHORT,
        )
    else:
        if action == Action.CLOSE:
            short_params["reduceOnly"] = True

    transacted_size = 0

    async for price_data in stream_price_diff(
        buy_exchange=long_exchange if action == Action.OPEN else short_exchange,
        sell_exchange=short_exchange if action == Action.OPEN else long_exchange,
        buy_symbol=long_symbol if action == Action.OPEN else short_symbol,
        sell_symbol=short_symbol if action == Action.OPEN else long_symbol,
        update_interval=1.0,
        log_updates=False,
    ):
        if time.time() - start_time > timeout:
            logger.info("Arbitrage order timed out.")
            break

        if not price_data.spread_percentage > threshold:
            logger.info(
                f"Waiting for arbitrage opportunity... {price_data}, {threshold}"
            )
            continue

        remaining_size = total_size - transacted_size
        if remaining_size <= 0:
            break

        current_order_size = min(
            price_data.best_ask_size,
            price_data.best_bid_size,
            remaining_size,
        )
        try:
            current_order_size = float(
                max(
                    long_exchange.amount_to_precision(long_symbol, current_order_size),
                    short_exchange.amount_to_precision(
                        short_symbol, current_order_size
                    ),
                )
            )
        except InvalidOrder as e:
            logger.warning(f"Skipping order due to precision error: {e}")
            continue

        long_notional = current_order_size * price_data.best_ask
        short_notional = current_order_size * price_data.best_bid
        min_long_notional = long_exchange.market(long_symbol)["limits"]["cost"]["min"]
        min_short_notional = short_exchange.market(short_symbol)["limits"]["cost"][
            "min"
        ]

        if min_long_notional is not None and long_notional < min_long_notional:
            logger.warning(
                f"Skipping arbitrage order due to minimum notional requirement on {long_exchange.__class__.__name__}: {min_long_notional}"
            )
            continue
        if min_short_notional is not None and short_notional < min_short_notional:
            logger.warning(
                f"Skipping arbitrage order due to minimum notional requirement on {short_exchange.__class__.__name__}: {min_short_notional}"
            )
            continue

        logger.info(
            f"Arbitrage opportunity detected: {price_data}. Placing orders of size {current_order_size} {symbol} "
            f"({transacted_size}/{total_size} completed)"
        )

        # Place limit orders at best prices
        await asyncio.gather(
            long_exchange.create_order(
                symbol=long_symbol,
                type="market",
                side="buy" if action == Action.OPEN else "sell",
                amount=current_order_size,
                params=long_params,
            ),
            short_exchange.create_order(
                symbol=short_symbol,
                type="market",
                side="sell" if action == Action.OPEN else "buy",
                amount=current_order_size,
                params=short_params,
            ),
        )

        transacted_size += float(current_order_size)
        logger.info(
            f"Successfully placed arbitrage orders of size {current_order_size} {symbol} "
            f"({transacted_size}/{total_size} completed)"
        )

    logger.info("Arbitrage order completed.")
