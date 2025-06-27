# Changelog

All notable changes to the quantjourney-bidask project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.9.0] - 2024-06-24

### Added
- Initial release of quantjourney-bidask package
- EDGE (Efficient estimator of bid-ask spreads) implementation based on Ardia, Guidotti & Kroencke (2024)
- Core functionality:
  - `edge()`: Single spread estimate from OHLC data
  - `edge_rolling()`: Rolling window spread estimates with vectorized operations
  - `edge_expanding()`: Expanding window spread estimates
- Data fetching capabilities:
  - `fetch_yfinance_data()`: Yahoo Finance integration via yfinance
  - `fetch_binance_data()`: Binance API integration via custom FastAPI server
- Real-time monitoring:
  - `LiveSpreadMonitor`: WebSocket-based real-time spread monitoring
  - Configurable alert thresholds and callbacks
  - Multi-symbol support for cryptocurrency pairs
- Comprehensive examples:
  - Basic spread estimation with synthetic and real data
  - Animated spread monitoring for presentations
  - Multi-cryptocurrency spread comparison analysis
  - Liquidity risk monitoring with statistical alerts
  - Real-time WebSocket implementation examples
- Professional documentation:
  - Detailed docstrings following NumPy style
  - Academic paper validation (matches expected results)
  - Usage examples with both synthetic and real market data
- Testing framework:
  - Unit tests for core functionality
  - Validation against original research paper results
  - Edge case handling (missing data, insufficient observations)

### Technical Details
- Implements the methodology from "Efficient estimation of bid–ask spreads from open, high, low, and close prices" (Journal of Financial Economics, 2024)
- Vectorized operations for high-performance rolling calculations
- Proper handling of missing values and edge cases
- Support for multiple data frequencies (minute, hourly, daily)
- WebSocket integration for real-time cryptocurrency data
- Modern Python packaging with pyproject.toml

### Dependencies
- numpy >= 1.20
- pandas >= 1.5
- requests >= 2.28
- yfinance >= 0.2
- matplotlib >= 3.5
- plotly >= 5.0
- websocket-client >= 1.0

### Author
- Jakub Polec (jakub@quantjourney.pro)
- QuantJourney

### License
- MIT License