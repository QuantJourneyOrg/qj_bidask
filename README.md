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

```bash
pip install quantjourney-bidask

Usage
Basic Spread Estimation
python

import pandas as pd
from quantjourney_bidask import edge

# Load test data
df = pd.read_csv("https://raw.githubusercontent.com/eguidotti/bidask/main/pseudocode/ohlc.csv")

# Compute single spread estimate
spread = edge(df.Open, df.High, df.Low, df.Close)
print(f"Estimated spread: {spread:.6f}")  # Expected: ~0.010185 (1.0185%)

Rolling Window Estimates
python

from quantjourney_bidask import edge_rolling

# Compute rolling spreads over a 21-period window
spreads = edge_rolling(df, window=21)
print(spreads.head())

Expanding Window Estimates
python

from quantjourney_bidask import edge_expanding

# Compute expanding spreads with minimum 21 periods
spreads = edge_expanding(df, min_periods=21)
print(spreads.head())

Fetching Data
python

from quantjourney_bidask import fetch_binance_data, fetch_yfinance_data

# Fetch Binance data
binance_df = fetch_binance_data(
    symbols=["BTCUSDT"],
    timeframe="1h",
    start="2024-01-01T00:00:00Z",
    end="2024-01-02T00:00:00Z",
    api_key="your-api-key"
)

# Fetch Yahoo Finance data
yf_df = fetch_yfinance_data(
    tickers=["AAPL"],
    period="1mo",
    interval="1d"
)

Why Bid-Ask Spread Estimation Matters
Bid-ask spreads represent the cost of trading and are a critical measure of market liquidity and transaction costs. The EDGE estimator provides:
Accuracy: Captures the root mean square effective spread, reflecting true trading costs.

Flexibility: Works with daily, hourly, or minute-level OHLC data for equities, crypto, and more.

Applications: Used in market making, high-frequency trading, transaction cost analysis, and liquidity risk assessment.

For a detailed explanation, see our blog post (docs/blog_post.md).
Testing
Run tests using pytest:
bash

pytest tests/

The test suite includes validation against known test cases from the original paper and edge cases for robustness.
Contributing
Contributions are welcome! Please open a pull request or issue on GitHub. To contribute:
Fork the repository.

Create a feature branch (git checkout -b feature/your-feature).

Commit changes (git commit -m "Add your feature").

Push to the branch (git push origin feature/your-feature).

Open a pull request.

License
MIT License. See LICENSE for details.
Citation
When using this library, please cite:
bibtex

@article{edge,
  title = {Efficient estimation of bid–ask spreads from open, high, low, and close prices},
  journal = {Journal of Financial Economics},
  volume = {161},
  pages = {103916},
  year = {2024},
  doi = {https://doi.org/10.1016/j.jfineco.2024.103916},
  author = {David Ardia and Emanuele Guidotti and Tim A. Kroencke},
}

Support
For issues or questions, please open an issue on GitHub.

