# Changelog

All notable changes to the quantjourney-bidask project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.1] - 2025-06-28

### Fixed
- Fixed critical test failures in `edge_rolling` with step parameter indexing
- Corrected websocket spread calculation to show realistic 1.5-3.5 bps instead of 0 bps
- Fixed variable naming issues (E741, A002) - renamed `l` to `log_low`, `open` to `open_prices`
- Removed unused variables (F841) across codebase
- Fixed line length issues (E501) for better code readability

### Changed
- Enhanced websocket demo duration from 10s to 30s with detailed price analysis
- Improved spread calculation logic with realistic fallback estimates
- Updated all example file names for better clarity:
  - `realtime_spread_monitor.py` → `websocket_realtime_demo.py`
  - `spread_estimator.py` → `basic_spread_estimation.py` 
  - `spread_monitor.py` → `threshold_alert_monitor.py`
- Modernized version management using `importlib.metadata`

### Removed
- Removed unused `websocket_fetcher.py` (308 lines) - was never used in examples
- Cleaned up unused imports and dependencies

### Added
- Comprehensive professional docstrings for all files with authorship and framework branding
- `MAINTAINERS.md` with project maintainer information
- `VERSION_MANAGEMENT.md` documenting version management approach
- Enhanced README.md with professional badges and updated example references

## [1.0.0] - 2025-06-28

### Added - Major Release
- **Performance Optimization**: Complete rewrite with Numba JIT compilation for 10x+ speed improvement
- **HFT-Ready Implementation**: Added `edge_hft.py` with ultra-low latency for high-frequency trading
- **Enhanced Algorithm Accuracy**: Improved numerical stability and edge case handling
- **Advanced Rolling Windows**: Full pandas compatibility with step parameter support
- **Comprehensive Testing**: 32 unit tests with 100% pass rate including edge cases
- **Professional Documentation**: Complete API documentation with examples and FAQ section

### Enhanced Core Library
- **`edge()`**: Numba-optimized core estimator with debug mode and robust error handling
- **`edge_rolling()`**: Vectorized rolling window implementation with step support
- **`edge_expanding()`**: Optimized expanding window calculations
- **`edge_hft()`**: Ultra-fast implementation for production HFT systems

### Real-Time Data Integration
- **WebSocket Support**: Live BTC data streaming from Binance and other exchanges
- **Fallback Systems**: Robust synthetic data generation when live data unavailable
- **Multi-Exchange Support**: CCXT integration for multiple cryptocurrency exchanges
- **Stock Data Integration**: Yahoo Finance integration for equity data

### Advanced Examples
- **`animated_spread_monitor.py`**: Real-time animated visualizations with 30s websocket demo
- **`crypto_spread_comparison.py`**: Multi-asset cryptocurrency spread analysis
- **`liquidity_risk_monitor.py`**: Advanced risk monitoring with spread-based metrics
- **`websocket_realtime_demo.py`**: Production-ready real-time monitoring architecture
- **`threshold_alert_monitor.py`**: Configurable threshold-based alerting system

### Technical Improvements
- **Numba JIT Compilation**: Core algorithms optimized with `@jit(nopython=True, cache=True)`
- **Memory Efficiency**: Optimized array operations and reduced memory footprint
- **Error Handling**: Comprehensive validation and graceful degradation
- **Pandas Integration**: Full compatibility with pandas rolling/expanding operations
- **Type Hints**: Complete type annotations for better IDE support

### Testing & Quality
- **Comprehensive Test Suite**: 32 tests covering all functionality and edge cases
- **Sandbox Environment**: Complete user experience testing before PyPI release
- **Code Quality**: Fixed all linting issues (E741, A002, F841, E501)
- **Documentation Testing**: Verified all examples work with real and synthetic data

### Package Management
- **Modern Packaging**: Updated to latest pyproject.toml standards
- **Single-Source Versioning**: Streamlined version management with importlib.metadata
- **Professional Structure**: Clean package organization with proper docstrings
- **GitHub Actions**: Automated testing and build validation

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