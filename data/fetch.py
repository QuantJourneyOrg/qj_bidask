"""
Simplified data fetcher for quantjourney_bidask examples and tests.

Provides data fetching capabilities for stock and cryptocurrency data with
websocket support for real-time BTC streaming.

Author: Jakub Polec
Date: 2025-06-28

Part of the QuantJourney framework - The framework with advanced quantitative 
finance tools and insights.
"""

import asyncio
import logging
import os
from datetime import datetime, timedelta, timezone

import numpy as np
import pandas as pd
import yfinance as yf

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    import ccxt
    import ccxt.async_support as ccxt_async

    CCXT_AVAILABLE = True
except ImportError:
    CCXT_AVAILABLE = False
    logger.warning("CCXT not available - crypto features will use synthetic data")


class DataFetcher:

    def __init__(self, data_dir: str = "data"):
        self.data_dir = data_dir
        os.makedirs(data_dir, exist_ok=True)
        logger.info(f"DataFetcher initialized: data_dir={data_dir}")

    async def get_btc_1m_websocket(
        self, exchange_name: str = "binance", duration_seconds: int = 60
    ):
        """Get real-time BTC data via CCXT - fetches live data every second."""
        if not CCXT_AVAILABLE:
            logger.info("CCXT not available, using synthetic BTC data")
            return self._generate_synthetic_btc_stream(duration_seconds)

        try:
            exchange_class = getattr(ccxt_async, exchange_name.lower())
            exchange = exchange_class({"enableRateLimit": True, "timeout": 10000})
            await exchange.load_markets()

            data_points = []
            symbol = "BTC/USDT"

            logger.info(
                f"🚀 Starting BTC real-time data stream for {duration_seconds}s "
                f"using {exchange_name}"
            )

            for i in range(duration_seconds):
                try:
                    # Fetch real-time ticker data
                    ticker = await exchange.fetch_ticker(symbol)

                    # Calculate spread from bid/ask if available
                    price = float(ticker["close"])
                    bid = ticker.get("bid")
                    ask = ticker.get("ask")

                    if bid and ask and bid > 0 and ask > 0:
                        # Real bid-ask spread
                        spread_value = float(ask) - float(bid)
                        # If real spread is 0 or very small, use estimated
                        # spread instead
                        # Less than 0.1 bps
                        if spread_value < price * 0.000001:
                            # 2 basis points realistic spread
                            base_spread_bps = 2.0
                            volatility_factor = 1 + np.random.uniform(-0.3, 0.7)
                            spread_bps = base_spread_bps * volatility_factor
                            spread_value = price * (spread_bps / 10000)
                            spread_source = "estimated"
                        else:
                            spread_source = "real"
                    else:
                        # Estimate realistic spread for BTC (typically 1-5 bps)
                        base_spread_bps = 2.5  # 2.5 basis points base spread
                        volatility_factor = 1 + np.random.uniform(
                            -0.5, 1.0
                        )  # Add some randomness
                        spread_bps = base_spread_bps * volatility_factor
                        spread_value = price * (spread_bps / 10000)
                        spread_source = "estimated"

                    current_time = datetime.now(timezone.utc)
                    data_points.append(
                        {
                            "timestamp": current_time,
                            "symbol": "BTCUSDT",
                            "price": price,
                            "open": (
                                float(ticker["open"]) if ticker.get("open") else price
                            ),
                            "high": (
                                float(ticker["high"]) if ticker.get("high") else price
                            ),
                            "low": float(ticker["low"]) if ticker.get("low") else price,
                            "close": price,
                            "volume": (
                                float(ticker["baseVolume"])
                                if ticker.get("baseVolume")
                                else 0
                            ),
                            "bid": float(bid) if bid else price - spread_value / 2,
                            "ask": float(ask) if ask else price + spread_value / 2,
                            "spread": spread_value / price,  # As percentage
                            "spread_source": spread_source,
                        }
                    )

                    spread_bps = (spread_value / price) * 10000
                    if i % 5 == 0:  # Log every 5 seconds
                        logger.info(
                            f"Real BTC: ${price:.2f}, spread: "
                            f"{spread_bps:.2f}bps ({spread_source})"
                        )

                    await asyncio.sleep(1)

                except Exception as e:
                    logger.warning(f"Fetch ticker error: {e}")
                    # Continue trying for a few more attempts
                    if i < duration_seconds - 5:
                        await asyncio.sleep(1)
                        continue
                    else:
                        break

            await exchange.close()

            # If we got some real data, return it
            if data_points:
                df = pd.DataFrame(data_points)
                logger.info(
                    f"Collected {len(data_points)} real BTC data points "
                    f"from {exchange_name}"
                )
                return df
            else:
                logger.info("No real data collected, falling back to synthetic")
                return self._generate_synthetic_btc_stream(duration_seconds)

        except Exception as e:
            logger.error(f"Real-time data error: {e}")
            logger.info("Falling back to synthetic data")
            return self._generate_synthetic_btc_stream(duration_seconds)

    async def get_historical_crypto_data(
        self,
        symbol: str = "BTC/USDT",
        exchange: str = "binance",
        timeframe: str = "1m",
        limit: int = 100,
    ):
        """Get historical crypto data."""
        if not CCXT_AVAILABLE:
            return self._generate_synthetic_historical_data(symbol, limit)

        try:
            exchange_class = getattr(ccxt_async, exchange.lower())
            exchange_instance = exchange_class(
                {"enableRateLimit": True, "timeout": 30000}
            )
            await exchange_instance.load_markets()

            ohlcv = await exchange_instance.fetch_ohlcv(symbol, timeframe, limit=limit)
            await exchange_instance.close()

            if not ohlcv:
                logger.warning(f"No historical data for {symbol}")
                return self._generate_synthetic_historical_data(symbol, limit)

            df = pd.DataFrame(
                ohlcv, columns=["timestamp", "open", "high", "low", "close", "volume"]
            )
            df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms", utc=True)
            df["symbol"] = symbol.replace("/", "")

            logger.info(f"Fetched {len(df)} historical data points for {symbol}")
            return df

        except Exception as e:
            logger.error(f"Historical data error: {e}")
            return self._generate_synthetic_historical_data(symbol, limit)

    def get_stock_data(self, ticker: str, period: str = "1mo", interval: str = "1d"):
        """Get stock data via yfinance."""
        try:
            stock = yf.Ticker(ticker)
            df = stock.history(period=period, interval=interval)

            if df.empty:
                logger.warning(f"No stock data for {ticker}")
                return pd.DataFrame()

            df = df.reset_index()
            df["timestamp"] = (
                pd.to_datetime(df["Date"], utc=True)
                if "Date" in df.columns
                else pd.to_datetime(df["Datetime"], utc=True)
            )
            df["symbol"] = ticker
            df.columns = [col.lower() for col in df.columns]

            cols = ["timestamp", "symbol", "open", "high", "low", "close", "volume"]
            df = df[[col for col in cols if col in df.columns]]

            logger.info(f"Fetched {len(df)} stock data points for {ticker}")
            return df

        except Exception as e:
            logger.error(f"Stock data error for {ticker}: {e}")
            return pd.DataFrame()

    def save_data(self, df: pd.DataFrame, filename: str):
        """Save data to CSV."""
        if not filename.endswith(".csv"):
            filename += ".csv"
        filepath = os.path.join(self.data_dir, filename)

        try:
            df.to_csv(filepath, index=False)
            logger.info(f"Data saved to {filepath}")
            return filepath
        except Exception as e:
            logger.error(f"Save error: {e}")
            raise

    def load_data(self, filename: str):
        """Load data from CSV."""
        if not filename.endswith(".csv"):
            filename += ".csv"
        filepath = os.path.join(self.data_dir, filename)

        try:
            df = pd.read_csv(filepath)
            if "timestamp" in df.columns:
                df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True)
            logger.info(f"Data loaded from {filepath}")
            return df
        except Exception as e:
            logger.error(f"Load error: {e}")
            raise

    def _generate_synthetic_btc_stream(self, duration_seconds: int):
        """Generate synthetic BTC stream data with realistic price movements."""
        base_price = 45000
        data_points = []
        current_time = datetime.now(timezone.utc)

        logger.info(
            f"Generating synthetic BTC data with realistic price movements "
            f"for {duration_seconds}s"
        )

        for i in range(duration_seconds):
            # More realistic price movement with trend and volatility
            trend = 0.0001 if i > duration_seconds / 2 else -0.0001  # Slight trend
            volatility = base_price * 0.0005  # 0.05% volatility per second
            price_change = np.random.normal(trend * base_price, volatility)
            price = max(base_price + price_change, 1000)

            # Dynamic spread based on volatility
            base_spread_bps = 1.5  # 1.5 basis points base spread
            volatility_multiplier = 1 + abs(price_change) / (base_price * 0.001)
            spread_bps = base_spread_bps * volatility_multiplier
            spread_value = price * (spread_bps / 10000)

            data_points.append(
                {
                    "timestamp": current_time + timedelta(seconds=i),
                    "symbol": "BTCUSDT",
                    "price": price,
                    "open": base_price,
                    "high": max(base_price, price),
                    "low": min(base_price, price),
                    "close": price,
                    "volume": np.random.uniform(500, 2000),
                    "bid": price - spread_value / 2,
                    "ask": price + spread_value / 2,
                    "spread": spread_value / price,  # As percentage
                }
            )

            if i % 10 == 0:  # Log every 10 seconds
                logger.info(
                    f"Synthetic BTC: ${price:.2f} "
                    f"(change: {((price/base_price-1)*100):+.3f}%), "
                    f"spread: {spread_bps:.2f}bps"
                )

            base_price = price  # Use current price as base for next

        min_price = min(d['price'] for d in data_points)
        max_price = max(d['price'] for d in data_points)
        logger.info(
            f"Generated {len(data_points)} synthetic BTC data points with "
            f"price range ${min_price:.2f}-${max_price:.2f}"
        )
        return pd.DataFrame(data_points)

    def _generate_synthetic_historical_data(self, symbol: str, limit: int):
        """Generate synthetic historical OHLCV data."""
        base_price = 45000 if "BTC" in symbol.upper() else 2500
        data_points = []
        current_time = datetime.now(timezone.utc) - timedelta(minutes=limit)

        for i in range(limit):
            # Generate realistic OHLCV data
            price_change = np.random.normal(0, base_price * 0.005)
            close_price = max(base_price + price_change, 1)

            open_price = base_price
            high_price = max(open_price, close_price) * (
                1 + np.random.uniform(0, 0.002)
            )
            low_price = min(open_price, close_price) * (1 - np.random.uniform(0, 0.002))
            volume = np.random.uniform(1000, 10000)

            data_points.append(
                {
                    "timestamp": current_time + timedelta(minutes=i),
                    "symbol": symbol.replace("/", ""),
                    "open": open_price,
                    "high": high_price,
                    "low": low_price,
                    "close": close_price,
                    "volume": volume,
                }
            )
            base_price = close_price

        logger.info(f"Generated {len(data_points)} synthetic historical data points")
        return pd.DataFrame(data_points)


# Convenience functions for backward compatibility
async def get_crypto_data(
    symbol: str = "BTC/USDT",
    exchange: str = "binance",
    timeframe: str = "1m",
    limit: int = 100,
):
    """Quick function to get crypto data."""
    fetcher = DataFetcher()
    return await fetcher.get_historical_crypto_data(symbol, exchange, timeframe, limit)


def get_stock_data(ticker: str, period: str = "1mo", interval: str = "1d"):
    """Quick function to get stock data."""
    fetcher = DataFetcher()
    return fetcher.get_stock_data(ticker, period, interval)


async def stream_btc_data(duration_seconds: int = 60):
    """Quick function to stream BTC data."""
    fetcher = DataFetcher()
    return await fetcher.get_btc_1m_websocket(duration_seconds=duration_seconds)


async def main():
    """Example usage."""
    fetcher = DataFetcher()

    print("Testing BTC websocket stream...")
    btc_stream = await fetcher.get_btc_1m_websocket(duration_seconds=10)
    print(f"BTC stream: {len(btc_stream)} rows")
    if not btc_stream.empty:
        print(btc_stream.head())

    print("\nTesting historical crypto data...")
    hist_data = await fetcher.get_historical_crypto_data("BTC/USDT", limit=20)
    print(f"Historical data: {len(hist_data)} rows")
    if not hist_data.empty:
        print(hist_data.head())

    print("\nTesting stock data...")
    stock_data = fetcher.get_stock_data("AAPL", period="5d")
    print(f"Stock data: {len(stock_data)} rows")
    if not stock_data.empty:
        print(stock_data.head())


if __name__ == "__main__":
    asyncio.run(main())
