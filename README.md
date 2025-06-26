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
from data.fetch import fetch_yfinance_data
from quantjourney_bidask import edge_rolling

# Fetch OHLC data for a stock
df = fetch_yfinance_data(["AAPL"], period="1mo", interval="1d")

# Calculate rolling spread from fetched data
spreads = edge_rolling(df, window=20)
print(f"AAPL average spread: {spreads.mean():.6f}")
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

## Examples

The `examples/` directory contains comprehensive examples:

- `spread_estimator.py` - Basic spread estimation examples
- `spread_monitor.py` - Spread monitoring with threshold alerts
- `realtime_spread_monitor.py` - Live websocket monitoring with animation
- `crypto_spread_comparison.py` - Multi-asset spread comparison
- `liquidity_risk_monitor.py` - Liquidity risk monitoring
- `stock_liquidity_risk.py` - Stock-specific liquidity analysis

Run any example:

```bash
python examples/spread_estimator.py
python examples/realtime_spread_monitor.py
```

## API Reference

### Core Functions

- `edge(open, high, low, close, sign=False)`: Single-period spread estimation
- `edge_rolling(df, window, min_periods=None)`: Rolling window estimation  
- `edge_expanding(df, min_periods=3)`: Expanding window estimation

### Data Fetching (`data/fetch.py`)

- `fetch_yfinance_data(tickers, period, interval)`: Fetch real market data from Yahoo Finance
- `generate_synthetic_crypto_data(symbols, hours, interval_minutes)`: Generate synthetic crypto data
- `fetch_binance_data(*args, **kwargs)`: Compatibility function (returns synthetic data)
- `create_realtime_stream(symbols, exchange)`: Create websocket data stream
- `create_spread_monitor(symbols, window)`: Create real-time spread monitor

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

## Academic Citation

If you use this library in academic research, please cite:

```bibtex
@article{ardia2024efficient,
  title={Efficient Estimation of Bid-Ask Spreads from Open, High, Low, and Close Prices},
  author={Ardia, David and Guidotti, Emanuele and Kroencke, Tim A},
  journal={Journal of Financial Economics},
  volume={161},
  pages={103916},
  year={2024},
  publisher={Elsevier}
}
```

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