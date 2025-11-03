from frarber.enums.exchange_type import ExchangeType


def derive_symbol(exchange: ExchangeType, symbol: str) -> str:
    match exchange:
        case ExchangeType.BINANCE_USDM:
            return f"{symbol}/USDT:USDT"
        case ExchangeType.BYBIT:
            return f"{symbol}/USDT:USDT"
        case ExchangeType.BITGET:
            return f"{symbol}/USDT:USDT"
        case ExchangeType.PHEMEX:
            return f"{symbol}/USDT:USDT"
        case ExchangeType.MEXC_USDTM:
            return f"{symbol}/USDT:USDT"
        case ExchangeType.MEXC:
            return f"{symbol}/USDT"
        case _:
            raise ValueError(f"Unsupported exchange: {exchange}")
