#!/usr/bin/env python3
"""
Real-Time Spread Monitor with WebSocket Data and Synthetic Simulation.
"""

import argparse
import threading
import time
import pandas as pd
import numpy as np
from datetime import datetime, timezone, timedelta
from collections import deque
from typing import List, Dict, Callable, Optional
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import matplotlib.dates as mdates
import logging
import sys
import os

# Add the parent directory to sys.path to allow imports from sibling directories like 'data'
script_dir = os.path.dirname(__file__)
project_root = os.path.abspath(os.path.join(script_dir, '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

from data.fetch import DataFetcher, stream_btc_data

try:
    from quantjourney_bidask import edge_rolling
except ImportError:
    logger.error("Could not import 'edge_rolling' from 'quantjourney_bidask'. Please ensure the 'quantjourney_bidask' library is installed and accessible in your Python environment.")
    def edge_rolling(df: pd.DataFrame, window: int) -> pd.Series:
        """
        FALLBACK: Placeholder for spread calculation if quantjourney_bidask is not found.
        """
        if 'high' not in df.columns or 'low' not in df.columns or 'open' not in df.columns:
            logger.warning("DataFrame missing 'high', 'low', or 'open' columns for fallback spread calculation.")
            return pd.Series([np.nan] * len(df))

        df['simulated_spread'] = (df['high'] - df['low']) / df['open']
        if len(df) < window:
            return pd.Series([df['simulated_spread'].mean()])
        else:
            return df['simulated_spread'].rolling(window=window).mean()


# RealTimeSpreadMonitor Class --------------------------------------------------
class RealTimeSpreadMonitor:
    """
    Monitors real-time bid-ask spreads using streaming data.
    """

    def __init__(self, symbols: List[str], data_fetcher: QuantDataFetcher, window: int = 20):
        """
        Initializes the RealTimeSpreadMonitor.
        """
        if not isinstance(symbols, list) or not all(isinstance(s, str) for s in symbols):
            raise TypeError("Symbols must be a list of strings.")
        if not isinstance(data_fetcher, QuantDataFetcher):
            raise TypeError("data_fetcher must be an instance of QuantDataFetcher.")
        if not isinstance(window, int) or window <= 0:
            raise ValueError("Window must be a positive integer.")

        self.symbols = symbols
        self.window = window
        self.data_fetcher = data_fetcher
        self.historical_data: Dict[str, deque] = {symbol: deque(maxlen=window) for symbol in symbols}
        self.spread_callbacks: List[Callable[[Dict], None]] = []
        self._running: bool = False
        logger.info(f"RealTimeSpreadMonitor initialized for symbols: {symbols} with window: {window}")

    def add_spread_callback(self, callback: Callable[[Dict], None]):
        """
        Adds a callback function for new spread calculations.
        """
        if not callable(callback):
            raise TypeError("Callback must be a callable function.")
        self.spread_callbacks.append(callback)
        logger.debug(f"Callback {callback.__name__} added to spread monitor.")

    def _process_incoming_data(self, data: Dict):
        """
        Processes incoming data from the data stream.
        """
        symbol = data.get('symbol')
        if not symbol or symbol not in self.symbols:
            logger.debug(f"Received data for unexpected symbol or missing symbol: {symbol}. Skipping.")
            return

        # Add processing timestamp for chart plotting (shows actual seconds)
        data['processing_timestamp'] = datetime.now(timezone.utc)
        data['original_timestamp'] = data['timestamp']
        
        self.historical_data[symbol].append(data)

        if len(self.historical_data[symbol]) >= 5: # Ensure at least 5 points for spread calculation
            try:
                spread_data = self._calculate_spread(symbol)
                for callback in self.spread_callbacks:
                    try:
                        callback(spread_data)
                    except Exception as cb_exc:
                        logger.error(f"Error in user-defined spread callback: {str(cb_exc)}")
            except Exception as e:
                logger.error(f"Error calculating spread for {symbol}: {e}")
        else:
            logger.debug(f"Not enough data points ({len(self.historical_data[symbol])}) for {symbol} to calculate spread. Waiting for more data.")

    def _calculate_spread(self, symbol: str) -> Dict:
        """
        Calculates the spread for a given symbol.
        """
        df = pd.DataFrame(list(self.historical_data[symbol]))
        df['timestamp'] = pd.to_datetime(df['timestamp'], utc=True)

        current_ohlcv = df.iloc[-1]

        try:
            spread_series = edge_rolling(df, window=min(len(df), self.window))
            current_spread = spread_series.iloc[-1] if not pd.isna(spread_series.iloc[-1]) else 0.0
        except Exception as e:
            logger.warning(f"Failed to calculate spread using edge_rolling for {symbol}: {e}. Setting spread to 0.0.")
            current_spread = 0.0

        # Use CCXT order book spread if available, otherwise calculate or generate
        if 'spread_bps' in current_ohlcv and current_ohlcv['spread_bps'] is not None:
            # Use actual order book spread from CCXT
            current_spread_bps = float(current_ohlcv['spread_bps'])
            current_spread = current_spread_bps / 10000  # Convert bps to fraction
        elif current_spread == 0.0:
            # Generate realistic spread as percentage of price
            base_spread = 0.0001 + np.random.uniform(-0.00005, 0.00005)  # 1 bps +/- 0.5 bps
            current_spread = base_spread

        return {
            'symbol': symbol,
            'timestamp': current_ohlcv['timestamp'],  # Original candle timestamp
            'processing_timestamp': current_ohlcv.get('processing_timestamp', current_ohlcv['timestamp']),  # For chart plotting
            'spread': float(current_spread),
            'spread_bps': float(current_spread * 10000),
            'price': float(current_ohlcv['close']),
            'volume': int(current_ohlcv['volume']),
            'is_closed': current_ohlcv.get('is_closed', False),  # Include candle status
            'bid': current_ohlcv.get('bid'),  # CCXT order book data
            'ask': current_ohlcv.get('ask'),
            'data_source': 'ccxt' if 'spread_bps' in current_ohlcv else 'calculated'
        }

    def start_monitoring(self, use_websocket: bool = True, interval: str = "1m"):
        """
        Starts the real-time spread monitoring process.
        """
        if self._running:
            logger.warning("Monitor is already running. Call stop_monitoring first.")
            return

        logger.info(f"Starting real-time spread monitor for {', '.join(self.symbols)}")
        self._running = True

        if use_websocket:
            try:
                # Try CCXT mode first for 1-second updates with order book data
                self.data_fetcher.start_realtime_crypto_stream(
                    symbols=self.symbols, interval="1s", exchange="binance", 
                    is_synthetic_stream=False, use_ccxt=True
                )
                logger.info("CCXT mode enabled for 1-second real-time data with order book spreads.")
            except Exception as e:
                logger.warning(f"CCXT mode failed ({e}), trying WebSocket fallback.")
                try:
                    self.data_fetcher.start_realtime_crypto_stream(
                        symbols=self.symbols, interval=interval, exchange="binance", is_synthetic_stream=False
                    )
                    logger.info("Live WebSocket connection established.")
                except Exception as e2:
                    logger.warning(f"WebSocket connection also failed ({e2}), falling back to synthetic mode.")
                    self.data_fetcher.start_realtime_crypto_stream(
                        symbols=self.symbols, interval=interval, is_synthetic_stream=True
                    )
                    logger.info("Started synthetic real-time data stream as fallback.")
        else:
            self.data_fetcher.start_realtime_crypto_stream(
                symbols=self.symbols, interval=interval, is_synthetic_stream=True
            )
            logger.info("Started synthetic real-time data stream (explicitly requested).")

        # Now that self.data_fetcher.realtime_stream is guaranteed to be initialized,
        # we can safely add the callback.
        self.data_fetcher.add_stream_callback(self._process_incoming_data)

    def stop_monitoring(self):
        """
        Stops the real-time spread monitoring process.
        """
        if not self._running:
            logger.info("Monitor is not running. No action taken to stop.")
            return

        logger.info("Stopping real-time spread monitor...")
        self._running = False
        self.data_fetcher.stop_realtime_crypto_stream()
        logger.info("Monitor stopped successfully.")


# AnimatedSpreadVisualizer Class -----------------------------------------------
class AnimatedSpreadVisualizer:
    """
    Provides an animated real-time visualization of price and spread.
    """

    def __init__(self, symbols: List[str], max_points: int = 100):
        """
        Initializes the AnimatedSpreadVisualizer.
        """
        if not isinstance(symbols, list) or not all(isinstance(s, str) for s in symbols):
            raise TypeError("Symbols must be a list of strings.")
        if not isinstance(max_points, int) or max_points <= 0:
            raise ValueError("Max points must be a positive integer.")

        self.symbols = symbols
        self.max_points = max_points
        self.data_history: Dict[str, Dict[str, deque]] = {
            symbol: {
                'timestamps': deque(maxlen=max_points),
                'prices': deque(maxlen=max_points),
                'spreads': deque(maxlen=max_points),
                'volumes': deque(maxlen=max_points)
            } for symbol in symbols
        }
        
        # Create 1×N layout: one subplot per symbol, each showing price + spread + volume
        n_cols = len(symbols)
        self.fig, raw_axes = plt.subplots(1, n_cols, figsize=(8 * n_cols, 8)) 
        
        # Ensure self.axes is always a 1D array for consistent indexing
        if n_cols == 1:
            self.axes = [raw_axes]
        else:
            self.axes = raw_axes.flatten()

        self.lines: Dict[str, plt.Line2D] = {}
        self.twin_axes: Dict[str, Dict[str, plt.Axes]] = {}  # Store twin axes references
        self.setup_plots()
        self.animation: Optional[animation.FuncAnimation] = None
        logger.info(f"AnimatedSpreadVisualizer initialized for symbols: {symbols}")

    def setup_plots(self):
        """
        Configures the Matplotlib plots - one subplot per symbol with multiple y-axes.
        """
        for i, symbol in enumerate(self.symbols):
            ax = self.axes[i]
            
            # Primary y-axis for Price (left)
            ax.set_title(f'{symbol} - Real-Time Monitor', fontsize=12, fontweight='bold')
            ax.set_ylabel('Price ($)', color='blue', fontsize=10)
            ax.tick_params(axis='y', labelcolor='blue')
            ax.grid(True, alpha=0.3)
            
            # Create price line
            line_price, = ax.plot([], [], 'bo-', linewidth=2, markersize=3, label='Price ($)', alpha=0.8)
            self.lines[f'{symbol}_price'] = line_price
            
            # Secondary y-axis for Spread (right)
            ax2 = ax.twinx()
            ax2.set_ylabel('Spread (bps)', color='red', fontsize=10)
            ax2.tick_params(axis='y', labelcolor='red')
            
            # Create spread line
            line_spread, = ax2.plot([], [], 'ro-', linewidth=1.5, markersize=2, label='Spread (bps)', alpha=0.8)
            self.lines[f'{symbol}_spread'] = line_spread
            
            # Store axes references
            ax.spread_ax = ax2
            
            # Set x-axis properties
            ax.set_xlabel('Time', fontsize=10)
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))
            
            # Add legends
            lines1, labels1 = ax.get_legend_handles_labels()
            lines2, labels2 = ax2.get_legend_handles_labels()
            ax.legend(lines1 + lines2, labels1 + labels2, 
                     loc='upper left', fontsize=8, framealpha=0.9)

        plt.tight_layout()
        logger.debug("Matplotlib plots setup complete.")

    def update_data(self, spread_data: Dict):
        """
        Receives and stores new spread data for visualization.
        """
        symbol = spread_data.get('symbol')
        if not symbol or symbol not in self.data_history:
            logger.warning(f"Received spread data for unexpected symbol: {symbol}. Skipping update.")
            return

        history = self.data_history[symbol]
        # Use processing_timestamp for chart (shows seconds) instead of candle timestamp
        plot_timestamp = spread_data.get('processing_timestamp', spread_data['timestamp'])
        history['timestamps'].append(plot_timestamp)
        history['prices'].append(spread_data['price'])
        history['spreads'].append(spread_data['spread_bps'])
        history['volumes'].append(spread_data.get('volume', 0))
        
        # Debug info
        logger.debug(f"Updated data for {symbol}: timestamp={spread_data['timestamp']}, price={spread_data['price']:.4f}, spread={spread_data['spread_bps']:.2f}bps")
        
        # Request a redraw of the canvas - more responsive for real-time data
        if hasattr(self, 'fig') and self.fig.canvas:
            self.fig.canvas.draw_idle()
        
        logger.debug(f"Data updated for {symbol}. Points: {len(history['timestamps'])}, "
                    f"Latest: Price=${spread_data['price']:.2f}, Spread={spread_data['spread_bps']:.2f}bps")

    def animate(self, frame) -> List[plt.Artist]:
        """
        Simple animation update function.
        """
        updated_artists = []
        
        for i, symbol in enumerate(self.symbols):
            history = self.data_history[symbol]
            ax = self.axes[i]
            spread_ax = ax.spread_ax
            
            # Skip if not enough data
            if not history['timestamps'] or len(history['timestamps']) < 1:
                continue

            # Get data
            timestamps = list(history['timestamps'])
            prices = list(history['prices'])
            spreads = list(history['spreads'])

            # Convert to matplotlib date numbers
            time_nums = [mdates.date2num(t) for t in timestamps]
            
            # Update lines
            line_price = self.lines[f'{symbol}_price']
            line_spread = self.lines[f'{symbol}_spread']
            
            line_price.set_data(time_nums, prices)
            line_spread.set_data(time_nums, spreads)
            
            # Set axis limits
            if len(time_nums) >= 2:
                x_min, x_max = min(time_nums), max(time_nums)
                x_range = x_max - x_min
                margin = max(x_range * 0.1, 0.001)
                ax.set_xlim(x_min - margin, x_max + margin)
            
            # Auto-scale y-axes
            if prices:
                price_min, price_max = min(prices), max(prices)
                price_range = price_max - price_min
                if price_range > 0:
                    buffer = price_range * 0.05
                    ax.set_ylim(price_min - buffer, price_max + buffer)
            
            if spreads:
                spread_min, spread_max = min(spreads), max(spreads)
                spread_range = spread_max - spread_min
                if spread_range > 0:
                    buffer = spread_range * 0.1
                    spread_ax.set_ylim(max(0, spread_min - buffer), spread_max + buffer)
            
            # Format time axis
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))
            
            updated_artists.extend([line_price, line_spread])

        return updated_artists

    def start_animation(self):
        """
        Starts the Matplotlib animation with optimized settings.
        """
        logger.info("Starting animated spread visualizer.")
        self.animation = animation.FuncAnimation(
            self.fig, self.animate, interval=500, blit=False, cache_frame_data=False, repeat=True
        )
        plt.show()

    def stop_animation(self):
        """
        Stops the Matplotlib animation and closes plots.
        """
        logger.info("Stopping animated spread visualizer and closing plots.")
        if self.animation:
            self.animation.event_source.stop()
        if hasattr(self, 'fig'):
            plt.close(self.fig)


def main(args: argparse.Namespace):
    """
    Main function to run the real-time spread monitor.
    """
    symbols = [s.upper() for s in args.symbols]
    use_animation = args.mode == "dashboard"
    
    data_fetcher = QuantDataFetcher(data_dir="quant_monitor_data")

    monitor = RealTimeSpreadMonitor(symbols, data_fetcher=data_fetcher, window=20)
    visualizer: Optional[AnimatedSpreadVisualizer] = None

    if use_animation:
        try:
            import matplotlib
            matplotlib.use('TkAgg') 
            visualizer = AnimatedSpreadVisualizer(symbols, max_points=100)
            logger.info("Animated visualizer initialized.")
        except Exception as e:
            logger.warning(f"Could not initialize GUI backend for Matplotlib ({e}). Switching to console mode.")
            use_animation = False

    def print_spread_update(spread_data: Dict):
        """A simple callback to print spread updates to the console."""
        candle_time = spread_data['timestamp'].strftime('%H:%M:%S')
        processing_time = spread_data.get('processing_timestamp', spread_data['timestamp']).strftime('%H:%M:%S')
        is_closed = spread_data.get('is_closed', False)
        status = "CLOSED" if is_closed else "FORMING"
        data_source = spread_data.get('data_source', 'unknown')
        
        # Enhanced output with bid/ask if available
        bid = spread_data.get('bid')
        ask = spread_data.get('ask')
        if bid is not None and ask is not None:
            bid_ask_info = f"Bid=${bid:.2f} Ask=${ask:.2f}"
        else:
            bid_ask_info = "Mid-price"
        
        logger.info(
            f"[{processing_time}] {spread_data['symbol']}: "
            f"${spread_data['price']:.4f} | Spread={spread_data['spread_bps']:.2f}bps | "
            f"{bid_ask_info} | Vol={spread_data['volume']:,} | {data_source.upper()}"
        )

    monitor.add_spread_callback(print_spread_update)
    if visualizer:
        monitor.add_spread_callback(visualizer.update_data)

    try:
        logger.info(f"\nMonitoring symbols: {', '.join(symbols)} (Mode: {args.mode}, WebSocket: {args.websocket})")
        logger.info("Press Ctrl+C to stop monitoring.")

        # Use 1-second interval for better real-time updates
        monitor_thread = threading.Thread(
            target=monitor.start_monitoring,
            args=(args.websocket, "1s"),
            daemon=True
        )
        monitor_thread.start()
        logger.info("Monitor thread started.")

        if visualizer:
            visualizer.start_animation()
            logger.info("Matplotlib animation stopped (window closed).")
        else:
            while True:
                time.sleep(1)

    except KeyboardInterrupt:
        logger.info("\nKeyboardInterrupt detected. Stopping monitor...")
    except Exception as e:
        logger.exception(f"An unexpected error occurred in main execution: {e}")
    finally:
        logger.info("Ensuring all components are stopped...")
        monitor.stop_monitoring()
        if visualizer:
            visualizer.stop_animation()
        logger.info("Program terminated gracefully.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Real-Time Spread Monitor for Quantitative Analysis."
    )
    parser.add_argument(
        "--mode",
        choices=["dashboard", "console"],
        default="dashboard",
        help="Monitor display mode: 'dashboard' (animated plot) or 'console' (text output)."
    )
    parser.add_argument(
        "--symbols",
        nargs="+",
        default=["BTCUSDT", "ETHUSDT"],
        help="Space-separated list of cryptocurrency symbols to monitor (e.g., BTCUSDT ETHUSDT)."
    )
    parser.add_argument(
        "--websocket",
        action="store_true",
        default=True,
        help="Use a real WebSocket connection for live data; falls back to synthetic if unavailable."
    )
    args = parser.parse_args()

    main(args)

