# FRArber - Funding Rate Arbitrage CLI

FRArber is a sophisticated cryptocurrency arbitrage trading bot designed to capitalize on funding rate differences across multiple exchanges. The CLI tool enables traders to execute arbitrage strategies by simultaneously opening long and short positions on different exchanges when profitable opportunities arise.

## Features

- **Multi-Exchange Support**: Works with exchanges including Binance, Bybit, Bitget, Phemex
- **Real-time Price Monitoring**: Stream live price differences between exchanges
- **Automated Arbitrage Execution**: Open and close arbitrage positions automatically
- **Configurable Thresholds**: Set custom price difference thresholds for trade execution
- **Async Performance**: Built with asyncio for high-performance concurrent operations
- **Type Safety**: Fully typed with Pydantic for reliable data validation

## Supported Exchanges

- Binance (USD-M Futures)
- Phemex
- Bybit
- Bitget

## Installation

### Prerequisites

- Python 3.11 (required)
- [UV](https://docs.astral.sh/uv/) package manager

### Install UV

First, install UV if you haven't already:

```bash
# On macOS and Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# On Windows
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# Or via pip
pip install uv
```

### Install FRArber

1. **Clone the repository** (if not already done):
   ```bash
   git clone https://github.com/cheunhong/frarber.git
   ```

2. **Install dependencies using UV**:
   ```bash
   uv sync
   ```

3. **Activate the virtual environment**:
   ```bash
   source .venv/bin/activate  # On macOS/Linux
   # or
   .venv\Scripts\activate     # On Windows
   ```

4. **Install the CLI globally** (optional):
   ```bash
   uv pip install -e .
   ```

## Configuration

Before using FRArber, you'll need to configure your exchange API credentials. Create configuration file with filename `frarber.yaml` in your working directory for each exchange you plan to use.

### Example Configuration (`frarber.yaml`)

```yaml
exchanges:
  binanceusdm:
    api_key: "BINANCE_API_KEY"
    api_secret: "BINANCE_SECRET_KEY"
    hedged_mode: true
  bybit:
    api_key: "BYBIT_API_KEY"
    api_secret: "BYBIT_SECRET_KEY"
    hedged_mode: true
  bitget:
    api_key: "BITGET_API_KEY"
    api_secret: "BITGET_SECRET_KEY"
    password: "BITGET_PASSWORD"
    hedged_mode: true
  phemex:
    api_key: "PHEMEX_API_KEY"
    api_secret: "PHEMEX_SECRET_KEY"
    hedged_mode: true
    slow: true
```

## Usage

FRArber provides three main commands:

### 1. Monitor Price Differences

Stream real-time price differences between two exchanges:

```bash
frarber price-diff [BUY_EXCHANGE] [SELL_EXCHANGE] [SYMBOL]
```

**Example:**
```bash
frarber price-diff binanceusdm bybit BTC/USDT
```

**Options:**
- `--update-interval`: Time between price updates in seconds (default: 1.0)
- `--log-updates / --no-log-updates`: Whether to log price updates (default: True)

### 2. Open Arbitrage Position

Execute an arbitrage trade by opening positions on two exchanges:

```bash
frarber open [LONG_EXCHANGE] [SHORT_EXCHANGE] [SYMBOL] [TOTAL_SIZE]
```

**Example:**
```bash
frarber open binanceusdm bybit BTC/USDT 0.1
```

**Options:**
- `--timeout`: Maximum time to wait for arbitrage completion in seconds (default: 1800)
- `--threshold`: Price difference threshold for arbitrage opportunity as decimal (default: 0.001)

### 3. Close Arbitrage Position

Close existing arbitrage positions:

```bash
frarber close [LONG_EXCHANGE] [SHORT_EXCHANGE] [SYMBOL] [TOTAL_SIZE]
```

**Example:**
```bash
frarber close binanceusdm bybit BTC/USDT 0.1
```

**Options:**
- `--timeout`: Maximum time to wait for arbitrage completion in seconds (default: 1800)
- `--threshold`: Price difference threshold for arbitrage opportunity as decimal (default: 0.001)

## Exchange Identifiers

Use these identifiers when specifying exchanges in commands:

| Exchange | Identifier |
|----------|------------|
| Binance Spot | `binance` |
| Binance COIN-M Futures | `binancecoinm` |
| Binance USD-M Futures | `binanceusdm` |
| Bybit | `bybit` |
| OKX | `okx` |
| Phemex | `phemex` |
| BitMEX | `bitmex` |
| Bitget | `bitget` |
| Bitunix | `bitunix` |
| Coinbase | `coinbase` |
| CoinEx | `coinex` |
| Coinw | `coinw` |
| Deribit | `deribit` |
| Gate.io | `gateio` |
| Gemini | `gemini` |
| Huobi | `huobi` |
| Hyperliquid | `hyperliquid` |
| Kraken | `kraken` |
| KuCoin Spot | `kucoin` |
| KuCoin Futures | `kucoinfutures` |
| MEXC | `mexc` |
| LBank | `lbank` |
| WOO | `woo` |
| Upbit | `upbit` |

## Development

### Running Tests

```bash
uv run pytest
```

### Code Formatting

```bash
uv run black .
uv run ruff check --fix .
```

## Risk Disclaimer

⚠️ **WARNING**: Cryptocurrency trading involves substantial risk of loss. Arbitrage trading can be particularly risky due to:

- **Market volatility**: Rapid price movements can turn profitable trades into losses
- **Execution risk**: Network latency and exchange downtime can affect trade execution
- **Funding costs**: Holding positions incurs funding fees that may offset profits
- **Technical risk**: Software bugs or configuration errors can lead to unexpected losses

Always:
- Start with small position sizes
- Test thoroughly in a sandbox environment
- Monitor your positions closely
- Never trade with money you can't afford to lose

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Support

If you encounter any issues or have questions, please open an issue on GitHub.