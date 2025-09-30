import asyncio
import time
from typing import AsyncGenerator

from ccxt.base.exchange import Exchange
from frarber.enums.exchange_type import ExchangeType
from loguru import logger
from pydantic import BaseModel, Field


class PriceDifferenceData(BaseModel):
    """Data structure for price difference information."""

    symbol: str = Field(..., description="Trading pair symbol")
    buy_exchange: ExchangeType = Field(..., description="Exchange to go buy on")
    sell_exchange: ExchangeType = Field(..., description="Exchange to go sell on")
    best_ask: float = Field(..., gt=0, description="Best ask price on buy exchange")
    best_bid: float = Field(..., gt=0, description="Best bid price on sell exchange")
    best_ask_size: float = Field(..., gt=0, description="Best ask size on buy exchange")
    best_bid_size: float = Field(
        ..., gt=0, description="Best bid size on sell exchange"
    )
    timestamp: float = Field(..., description="Unix timestamp when data was captured")

    def __str__(self) -> str:
        return (
            f"{self.symbol} | "
            f"Long Ask ({self.buy_exchange.value}): {self.best_ask:.6f} {self.best_ask_size:.4f} | "
            f"Short Bid ({self.sell_exchange.value}): {self.best_bid:.6f} {self.best_bid_size:.4f} | "
            f"Diff: {self.price_diff:.6f} ({self.spread_percentage:.4f}%)"
        )

    @property
    def price_diff(self) -> float:
        """Calculate the price difference (short bid - long ask)."""
        return self.best_bid - self.best_ask

    @property
    def mid_price(self) -> float:
        """Calculate the mid price between long ask and short bid."""
        return (self.best_ask + self.best_bid) / 2

    @property
    def spread_percentage(self) -> float:
        """Calculate the spread as a percentage of the mid price."""
        return (self.price_diff / self.mid_price) * 100


async def stream_price_diff(
    buy_exchange: Exchange,
    sell_exchange: Exchange,
    symbol: str,
    update_interval: float = 1.0,
    log_updates: bool = True,
) -> AsyncGenerator[PriceDifferenceData, None]:
    """
    Stream the price difference between the top ask of buy_exchange and top bid of sell_exchange.

    :param buy_exchange: Exchange to go long on (we monitor the ask price)
    :param sell_exchange: Exchange to go short on (we monitor the bid price)
    :param symbol: Trading pair symbol
    :param update_interval: Time between price updates in seconds
    :param log_updates: Whether to log price updates
    :yield: PriceDifferenceData objects with current price information
    """
    buy_exchange_type = ExchangeType(buy_exchange.__class__.__name__)
    sell_exchange_type = ExchangeType(sell_exchange.__class__.__name__)

    try:
        logger.info(
            f"Starting price difference stream for {symbol} | "
            f"Long: {buy_exchange_type} | Short: {sell_exchange_type}"
        )

        while True:
            try:
                # Fetch order books concurrently
                buy_orderbook, sell_orderbook = await asyncio.gather(
                    buy_exchange.watch_order_book(symbol),
                    sell_exchange.watch_order_book(symbol),
                    return_exceptions=True,
                )

                best_ask = buy_orderbook["asks"][0][0]  # Best ask price
                best_ask_size = buy_orderbook["asks"][0][1]  # Best ask size

                best_bid = sell_orderbook["bids"][0][0]  # Best bid price
                best_bid_size = sell_orderbook["bids"][0][1]  # Best bid size

                # Create data object
                price_data = PriceDifferenceData(
                    symbol=symbol,
                    buy_exchange=buy_exchange_type,
                    sell_exchange=sell_exchange_type,
                    best_ask=best_ask,
                    best_bid=best_bid,
                    best_ask_size=best_ask_size,
                    best_bid_size=best_bid_size,
                    timestamp=time.time(),
                )

                if log_updates:
                    logger.info(str(price_data))

                yield price_data

            except Exception as e:
                logger.error(f"Error in price difference stream: {e}")
                await asyncio.sleep(update_interval)
                continue

            await asyncio.sleep(update_interval)

    finally:
        # Clean up connections
        await buy_exchange.close()
        await sell_exchange.close()
        logger.info("Price difference stream closed")
