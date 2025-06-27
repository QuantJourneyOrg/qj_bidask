# QuantJourney Bid-Ask Spread Estimator

![PyPI](https://img.shields.io/pypi/v/quantjourney-bidask)
![License](https://img.shields.io/github/license/quantjourney/bidask)
![Tests](https://img.shields.io/github/workflow/status/quantjourney/bidask/Test)

The `quantjourney-bidask` library provides an efficient estimator for calculating bid-ask spreads from open, high, low, and close (OHLC) prices, based on the methodology described in:

> Ardia, D., Guidotti, E., Kroencke, T.A. (2024). Efficient Estimation of Bid-Ask Spreads from Open, High, Low, and Close Prices. *Journal of Financial Economics*, 161, 103916. [doi:10.1016/j.jfineco.2024.103916](https://doi.org/10.1016/j.jfineco.2024.103916)

This library is designed for quantitative finance professionals, researchers, and traders who need accurate and computationally efficient spread estimates for equities, cryptocurrencies, and other assets.

## Features

- **Efficient Spread Estimation**: Implements the EDGE estimator for single, rolling, and expanding windows.
- **Real-Time Data**: Websocket support for live cryptocurrency data from Binance and other exchanges.
- **Data Integration**: Fetch OHLC data from Yahoo Finance and generate synthetic data for testing.
- **Live Monitoring**: Real-time spread monitoring with animated visualizations.
- **Local Development**: Works completely locally without cloud dependencies.
- **Robust Handling**: Supports missing values, non-positive prices, and various data frequencies.
- **Comprehensive Tests**: Extensive unit tests with known test cases from the original paper.
- **Clear Documentation**: Detailed docstrings and usage examples.

## Installation

Install the library via pip:

```bash
pip install quantjourney-bidask
```

For development (local setup):

```bash
git clone https://github.com/QuantJourneyOrg/qj_bidask
cd qj_bidask
pip install -e .
```

## Quick Start

### Basic Usage

```python
from quantjourney_bidask import edge

# Example OHLC data (as lists or numpy arrays)
open_prices = [100.0, 101.5, 99.8, 102.1, 100.9]
high_prices = [102.3, 103.0, 101.2, 103.5, 102.0]
low_prices = [99.5, 100.8, 98.9, 101.0, 100.1]
close_prices = [101.2, 100.2, 101.8, 100.5, 101.5]

# Calculate bid-ask spread
spread = edge(open_prices, high_prices, low_prices, close_prices)
print(f"Estimated bid-ask spread: {spread:.6f}")
```

### Rolling Window Analysis

```python
from quantjourney_bidask import edge_rolling
import pandas as pd

# Create DataFrame with OHLC data
df = pd.DataFrame({
    'open': open_prices,
    'high': high_prices,
    'low': low_prices,
    'close': close_prices
})

# Calculate rolling spreads with a 20-period window
rolling_spreads = edge_rolling(df, window=20)
print(f"Rolling spreads: {rolling_spreads}")
```

### Data Fetching Integration

```python
from data.fetch import get_stock_data, get_crypto_data
from quantjourney_bidask import edge_rolling
import asyncio

# Fetch stock data
stock_df = get_stock_data("AAPL", period="1mo", interval="1d")
stock_spreads = edge_rolling(stock_df, window=20)
print(f"AAPL average spread: {stock_spreads.mean():.6f}")

# Fetch crypto data (async)
async def get_crypto_spreads():
    crypto_df = await get_crypto_data("BTC/USDT", "binance", "1h", 168)
    crypto_spreads = edge_rolling(crypto_df, window=24)
    return crypto_spreads.mean()

crypto_avg_spread = asyncio.run(get_crypto_spreads())
print(f"BTC average spread: {crypto_avg_spread:.6f}")
```

### Real-time Data Streaming

```python
from data.fetch import DataFetcher
import asyncio

async def stream_btc_spreads():
    fetcher = DataFetcher()
    # Stream BTC data for 60 seconds
    btc_stream = await fetcher.get_btc_1m_websocket(duration_seconds=60)
    
    # Calculate spread from real-time data
    if not btc_stream.empty:
        avg_spread_pct = (btc_stream['spread'] / btc_stream['price']).mean() * 100
        print(f"Real-time BTC average spread: {avg_spread_pct:.4f}%")

asyncio.run(stream_btc_spreads())
```

### Real-Time Spread Monitoring

```python
from data.fetch import create_spread_monitor

# Create real-time spread monitor
monitor = create_spread_monitor(["BTCUSDT", "ETHUSDT"], window=20)

# Add callback for spread updates
def print_spread_update(spread_data):
    print(f"{spread_data['symbol']}: {spread_data['spread_bps']:.2f} bps")

monitor.add_spread_callback(print_spread_update)

# Start monitoring (uses websockets for live data)
monitor.start_monitoring("1m")
```

### Animated Real-Time Dashboard

```python
# Run the real-time dashboard
python examples/realtime_spread_monitor.py --mode dashboard

# Or console mode
python examples/realtime_spread_monitor.py --mode console
```

## Project Structure

```
quantjourney_bidask/
├── quantjourney_bidask/          # Main library code
│   ├── __init__.py
│   ├── edge.py                   # Core EDGE estimator
│   ├── edge_rolling.py           # Rolling window estimation
│   └── edge_expanding.py         # Expanding window estimation
├── data/
│   └── fetch.py                  # Simplified data fetcher for examples
├── examples/                     # Comprehensive usage examples
│   ├── simple_data_example.py    # Basic usage demonstration
│   ├── spread_estimator.py       # Spread estimation examples
│   ├── animated_spread_monitor.py # Animated visualizations
│   ├── crypto_spread_comparison.py # Crypto spread analysis
│   ├── liquidity_risk_monitor.py  # Risk monitoring
│   ├── realtime_spread_monitor.py # Live monitoring dashboard
│   └── stock_liquidity_risk.py    # Stock liquidity analysis
├── tests/                        # Unit tests (GitHub only)
│   ├── test_edge.py
│   ├── test_edge_rolling.py
│   └── test_data_fetcher.py
└── _output/                      # Example output images
    ├── simple_data_example.png
    ├── crypto_spread_comparison.png
    └── spread_estimator_results.png
```

## Examples and Visualizations

The package includes comprehensive examples with beautiful visualizations:

### Basic Data Analysis
![Crypto Spread Analysis](https://raw.githubusercontent.com/QuantJourneyOrg/qj_bidask/ad49bd78c82ab1c44561d0f2e707ae304575a147/_output/crypto_spread_comprehensive_analysis.png)

### Crypto Spread Comparison  
![Crypto Spread Comparison](https://raw.githubusercontent.com/QuantJourneyOrg/qj_bidask/refs/heads/main/_output/crypto_spread_comparison.png)

### Spread Estimation Results
![Spread Estimator Results](https://raw.githubusercontent.com/QuantJourneyOrg/qj_bidask/refs/heads/main/_output/spread_estimator_results.png)

### Running Examples

After installing via pip, examples are included in the package:

```python
import quantjourney_bidask
from pathlib import Path

# Find package location
pkg_path = Path(quantjourney_bidask.__file__).parent
examples_path = pkg_path.parent / 'examples'
print(f"Examples located at: {examples_path}")

# List available examples
for example in examples_path.glob('*.py'):
    print(f"📄 {example.name}")
```

Or clone the repository for full access to examples and tests:

```bash
git clone https://github.com/QuantJourneyOrg/qj_bidask
cd qj_bidask
python examples/simple_data_example.py
python examples/spread_estimator.py
python examples/crypto_spread_comparison.py
```

### Available Examples

- **`simple_data_example.py`** - Basic usage with stock and crypto data
- **`spread_estimator.py`** - Core spread estimation functionality
- **`animated_spread_monitor.py`** - Real-time animated visualizations
- **`crypto_spread_comparison.py`** - Multi-asset crypto analysis
- **`liquidity_risk_monitor.py`** - Risk monitoring and alerts
- **`realtime_spread_monitor.py`** - Live websocket monitoring dashboard
- **`stock_liquidity_risk.py`** - Stock-specific liquidity analysis

## Testing and Development

### Unit Tests
The package includes comprehensive unit tests (available in the GitHub repository):

- **`test_edge.py`** - Core EDGE estimator tests with known values from the academic paper
- **`test_edge_rolling.py`** - Rolling window estimation tests
- **`test_edge_expanding.py`** - Expanding window estimation tests  
- **`test_data_fetcher.py`** - Data fetching functionality tests
- **`test_estimators.py`** - Integration tests for all estimators

Tests verify accuracy against the original paper's test cases and handle edge cases like missing data, non-positive prices, and various market conditions.

### Development and Testing
For full development access including tests:

```bash
# Clone the repository
git clone https://github.com/QuantJourneyOrg/qj_bidask
cd qj_bidask

# Install in development mode
pip install -e .

# Run tests
python -m pytest tests/ -v

# Run specific test files
python -m pytest tests/test_edge.py -v
python -m pytest tests/test_data_fetcher.py -v

# Run examples
python examples/simple_data_example.py
python examples/spread_estimator.py
```

### Package vs Repository
- **PyPI Package** (`pip install quantjourney-bidask`): Includes core library, examples, and documentation
- **GitHub Repository**: Full development environment with tests, development tools, and additional documentation

## API Reference

### Core Functions

- `edge(open, high, low, close, sign=False)`: Single-period spread estimation
- `edge_rolling(df, window, min_periods=None)`: Rolling window estimation  
- `edge_expanding(df, min_periods=3)`: Expanding window estimation

### Data Fetching (`data/fetch.py`)

- `DataFetcher()`: Main data fetcher class
- `get_stock_data(ticker, period, interval)`: Fetch stock data from Yahoo Finance
- `get_crypto_data(symbol, exchange, timeframe, limit)`: Fetch crypto data via CCXT (async)
- `stream_btc_data(duration_seconds)`: Stream BTC data via websocket (async)
- `DataFetcher.get_btc_1m_websocket()`: Stream BTC 1-minute data
- `DataFetcher.get_historical_crypto_data()`: Get historical crypto OHLCV data
- `DataFetcher.save_data()` / `DataFetcher.load_data()`: Save/load data to CSV

### Real-Time Classes

- `RealTimeDataStream`: Websocket data streaming for live market data
- `RealTimeSpreadMonitor`: Real-time spread calculation and monitoring
- `AnimatedSpreadMonitor`: Animated real-time visualization

## Requirements

- Python >= 3.11
- numpy >= 1.20
- pandas >= 1.5
- requests >= 2.28
- yfinance >= 0.2
- matplotlib >= 3.5
- websocket-client >= 1.0

## WebSocket Support

The library supports real-time data via websockets:

- **Binance**: `wss://stream.binance.com:9443/ws/` (cryptocurrency data)
- **Fallback**: Synthetic data generation for testing when websockets unavailable

Real-time features:
- Live spread calculation
- Animated visualizations
- Threshold alerts
- Multi-symbol monitoring

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request. For major changes, please open an issue first to discuss what you would like to change.

### Development Setup

```bash
git clone https://github.com/QuantJourneyOrg/qj_bidask
cd qj_bidask
pip install -e ".[dev]"

# Run tests
pytest

# Run examples
python examples/realtime_spread_monitor.py
```

## Support

- **Documentation**: [GitHub Repository](https://github.com/QuantJourneyOrg/qj_bidask)
- **Issues**: [Bug Tracker](https://github.com/QuantJourneyOrg/qj_bidask/issues)
- **Contact**: jakub@quantjourney.pro