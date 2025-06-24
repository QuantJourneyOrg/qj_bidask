# QuantJourney Bid-Ask Spread Estimator

![PyPI](https://img.shields.io/pypi/v/quantjourney-bidask)
![License](https://img.shields.io/github/license/quantjourney/bidask)
![Tests](https://img.shields.io/github/workflow/status/quantjourney/bidask/Test)

The `quantjourney-bidask` library provides an efficient estimator for calculating bid-ask spreads from open, high, low, and close (OHLC) prices, based on the methodology described in:

> Ardia, D., Guidotti, E., Kroencke, T.A. (2024). Efficient Estimation of Bid-Ask Spreads from Open, High, Low, and Close Prices. *Journal of Financial Economics*, 161, 103916. [doi:10.1016/j.jfineco.2024.103916](https://doi.org/10.1016/j.jfineco.2024.103916)

This library is designed for quantitative finance professionals, researchers, and traders who need accurate and computationally efficient spread estimates for equities, cryptocurrencies, and other assets.

## Features

- **Efficient Spread Estimation**: Implements the EDGE estimator for single, rolling, and expanding windows.
- **Data Integration**: Fetch OHLC data from Binance (via custom FastAPI server) and Yahoo Finance (via yfinance).
- **Robust Handling**: Supports missing values, non-positive prices, and various data frequencies.
- **Comprehensive Tests**: Extensive unit tests with known test cases from the original paper.
- **Clear Documentation**: Detailed docstrings and usage examples.

## Installation

Install the library via pip:

```bash
pip install quantjourney-bidask
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

# Calculate rolling spreads with a 20-period window
rolling_spreads = edge_rolling(
    open_prices, high_prices, low_prices, close_prices, 
    window=20
)
print(f"Rolling spreads: {rolling_spreads}")
```

### Data Fetching Integration

```python
from quantjourney_bidask import fetch_yfinance_data, edge

# Fetch OHLC data for a stock
data = fetch_yfinance_data("AAPL", period="1mo", interval="1h")

# Calculate spread from fetched data
spread = edge(data['Open'], data['High'], data['Low'], data['Close'])
print(f"AAPL spread estimate: {spread:.6f}")
```

### Live Monitoring

```python
from quantjourney_bidask import LiveSpreadMonitor

# Monitor live spreads for cryptocurrency
monitor = LiveSpreadMonitor("BTCUSDT", window=100)
monitor.start()

# Get current spread estimate
current_spread = monitor.get_current_spread()
print(f"Current BTC/USDT spread: {current_spread:.6f}")

monitor.stop()
```

## API Reference

### Core Functions

- `edge(open, high, low, close, sign=False)`: Single-period spread estimation
- `edge_rolling(open, high, low, close, window, min_periods=None)`: Rolling window estimation
- `edge_expanding(open, high, low, close, min_periods=3)`: Expanding window estimation

### Data Fetching

- `fetch_yfinance_data(symbol, period, interval)`: Fetch data from Yahoo Finance
- `fetch_binance_data(symbol, interval, limit)`: Fetch data from Binance API

### Live Monitoring

- `LiveSpreadMonitor(symbol, window)`: Real-time spread monitoring via WebSocket

## Requirements

- Python >= 3.8
- numpy >= 1.20
- pandas >= 1.5
- requests >= 2.28
- yfinance >= 0.2

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

## Support

- **Documentation**: [GitHub Repository](https://github.com/QuantJourneyOrg/qj_bidask)
- **Issues**: [Bug Tracker](https://github.com/QuantJourneyOrg/qj_bidask/issues)
- **Contact**: jakub@quantjourney.pro
