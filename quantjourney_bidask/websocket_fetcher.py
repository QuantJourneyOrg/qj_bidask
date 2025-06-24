"""
WebSocket Live Data Fetcher

Real-time data fetching for cryptocurrency exchanges using WebSockets.
"""

import json
import threading
import time
import pandas as pd
import numpy as np
from datetime import datetime, timezone
from typing import Dict, List, Callable, Optional
import websocket
from collections import deque
from .edge_rolling import edge_rolling

class LiveSpreadMonitor:
    """
    Real-time spread monitoring using WebSocket connections.
    
    Supports Binance WebSocket streams for live OHLC data and real-time
    spread calculation with configurable alerts.
    """
    
    def __init__(self, symbols: List[str], window: int = 20, buffer_size: int = 1000):
        """
        Initialize the live spread monitor.
        
        Parameters
        ----------
        symbols : List[str]
            List of trading symbols to monitor (e.g., ['BTCUSDT', 'ETHUSDT'])
        window : int
            Rolling window size for spread calculation
        buffer_size : int
            Maximum number of candles to keep in memory
        """
        self.symbols = [s.lower() for s in symbols]
        self.window = window
        self.buffer_size = buffer_size
        
        # Data storage
        self.data_buffers = {symbol: deque(maxlen=buffer_size) for symbol in self.symbols}
        self.spread_buffers = {symbol: deque(maxlen=buffer_size) for symbol in self.symbols}
        
        # WebSocket connections
        self.ws_connections = {}
        self.running = False
        
        # Callbacks
        self.data_callbacks = []
        self.alert_callbacks = []
        
        # Alert thresholds (in basis points)
        self.alert_thresholds = {symbol: {'high': 100, 'low': 5} for symbol in self.symbols}
    
    def add_data_callback(self, callback: Callable):
        """Add callback function for new data events."""
        self.data_callbacks.append(callback)
    
    def add_alert_callback(self, callback: Callable):
        """Add callback function for alert events."""
        self.alert_callbacks.append(callback)
    
    def set_alert_threshold(self, symbol: str, high_bps: float, low_bps: float):
        """Set alert thresholds for a symbol (in basis points)."""
        symbol = symbol.lower()
        if symbol in self.alert_thresholds:
            self.alert_thresholds[symbol] = {'high': high_bps, 'low': low_bps}
    
    def _create_websocket_url(self, symbols: List[str]) -> str:
        """Create Binance WebSocket URL for multiple symbols."""
        streams = []
        for symbol in symbols:
            streams.append(f"{symbol}@kline_1m")  # 1-minute klines
        
        if len(streams) == 1:
            return f"wss://stream.binance.com:9443/ws/{streams[0]}"
        else:
            stream_string = "/".join(streams)
            return f"wss://stream.binance.com:9443/stream?streams={stream_string}"
    
    def _on_message(self, ws, message):
        """Handle incoming WebSocket messages."""
        try:
            data = json.loads(message)
            
            # Handle multi-stream format
            if 'stream' in data:
                stream_data = data['data']
                symbol = stream_data['s'].lower()
            else:
                stream_data = data
                symbol = stream_data['s'].lower()
            
            # Extract kline data
            kline = stream_data['k']
            is_closed = kline['x']  # Whether kline is closed
            
            if is_closed:  # Only process closed candles
                candle_data = {
                    'timestamp': pd.to_datetime(kline['t'], unit='ms'),
                    'symbol': symbol,
                    'open': float(kline['o']),
                    'high': float(kline['h']),
                    'low': float(kline['l']),
                    'close': float(kline['c']),
                    'volume': float(kline['v'])
                }
                
                self._process_candle(candle_data)
        
        except Exception as e:
            print(f"Error processing message: {e}")
    
    def _process_candle(self, candle_data: Dict):
        """Process new candle data and update spreads."""
        symbol = candle_data['symbol']
        
        # Add to buffer
        self.data_buffers[symbol].append(candle_data)
        
        # Calculate spread if we have enough data
        if len(self.data_buffers[symbol]) >= self.window:
            # Convert buffer to DataFrame for spread calculation
            df = pd.DataFrame(list(self.data_buffers[symbol])[-self.window:])
            
            # Calculate current spread
            try:
                current_spread = edge_rolling(df.tail(1), window=min(len(df), self.window)).iloc[-1]
                
                if not pd.isna(current_spread):
                    spread_bps = current_spread * 10000  # Convert to basis points
                    
                    spread_data = {
                        'timestamp': candle_data['timestamp'],
                        'symbol': symbol,
                        'spread_bps': spread_bps,
                        'price': candle_data['close']
                    }
                    
                    self.spread_buffers[symbol].append(spread_data)
                    
                    # Check for alerts
                    self._check_alerts(spread_data)
                    
                    # Notify callbacks
                    for callback in self.data_callbacks:
                        callback(candle_data, spread_data)
            
            except Exception as e:
                print(f"Error calculating spread for {symbol}: {e}")
    
    def _check_alerts(self, spread_data: Dict):
        """Check if spread triggers any alerts."""
        symbol = spread_data['symbol']
        spread_bps = spread_data['spread_bps']
        thresholds = self.alert_thresholds[symbol]
        
        alert_type = None
        if spread_bps > thresholds['high']:
            alert_type = 'HIGH'
        elif spread_bps < thresholds['low']:
            alert_type = 'LOW'
        
        if alert_type:
            alert_data = {
                'type': alert_type,
                'symbol': symbol,
                'spread_bps': spread_bps,
                'threshold': thresholds[alert_type.lower()],
                'timestamp': spread_data['timestamp'],
                'price': spread_data['price']
            }
            
            for callback in self.alert_callbacks:
                callback(alert_data)
    
    def _on_error(self, ws, error):
        """Handle WebSocket errors."""
        print(f"WebSocket error: {error}")
    
    def _on_close(self, ws, close_status_code, close_msg):
        """Handle WebSocket connection close."""
        print("WebSocket connection closed")
    
    def _on_open(self, ws):
        """Handle WebSocket connection open."""
        print(f"WebSocket connected for symbols: {', '.join(self.symbols)}")
    
    def start(self):
        """Start the live monitoring."""
        if self.running:
            print("Monitor is already running")
            return
        
        self.running = True
        
        # Create WebSocket URL
        ws_url = self._create_websocket_url(self.symbols)
        
        # Create WebSocket connection
        self.ws = websocket.WebSocketApp(
            ws_url,
            on_message=self._on_message,
            on_error=self._on_error,
            on_close=self._on_close,
            on_open=self._on_open
        )
        
        # Start WebSocket in a separate thread
        self.ws_thread = threading.Thread(target=self.ws.run_forever)
        self.ws_thread.daemon = True
        self.ws_thread.start()
        
        print("Live spread monitoring started...")
    
    def stop(self):
        """Stop the live monitoring."""
        if not self.running:
            return
        
        self.running = False
        if hasattr(self, 'ws'):
            self.ws.close()
        
        print("Live spread monitoring stopped.")
    
    def get_current_data(self) -> Dict[str, pd.DataFrame]:
        """Get current data for all symbols."""
        result = {}
        for symbol in self.symbols:
            if len(self.data_buffers[symbol]) > 0:
                result[symbol] = pd.DataFrame(list(self.data_buffers[symbol]))
        return result
    
    def get_current_spreads(self) -> Dict[str, pd.DataFrame]:
        """Get current spread data for all symbols."""
        result = {}
        for symbol in self.symbols:
            if len(self.spread_buffers[symbol]) > 0:
                result[symbol] = pd.DataFrame(list(self.spread_buffers[symbol]))
        return result

def create_live_dashboard_example():
    """
    Example of creating a live dashboard (console-based).
    """
    import time
    
    def data_callback(candle_data, spread_data):
        """Print new data to console."""
        symbol = spread_data['symbol'].upper()
        timestamp = spread_data['timestamp'].strftime('%H:%M:%S')
        price = spread_data['price']
        spread_bps = spread_data['spread_bps']
        
        print(f"[{timestamp}] {symbol}: ${price:.2f} | Spread: {spread_bps:.2f}bps")
    
    def alert_callback(alert_data):
        """Print alerts to console."""
        symbol = alert_data['symbol'].upper()
        alert_type = alert_data['type']
        spread_bps = alert_data['spread_bps']
        threshold = alert_data['threshold']
        timestamp = alert_data['timestamp'].strftime('%H:%M:%S')
        
        print(f"🚨 [{timestamp}] {alert_type} SPREAD ALERT for {symbol}: "
              f"{spread_bps:.2f}bps (threshold: {threshold}bps)")
    
    # Create monitor
    monitor = LiveSpreadMonitor(['BTCUSDT', 'ETHUSDT'], window=10)
    
    # Set custom thresholds
    monitor.set_alert_threshold('BTCUSDT', high_bps=50, low_bps=2)
    monitor.set_alert_threshold('ETHUSDT', high_bps=60, low_bps=3)
    
    # Add callbacks
    monitor.add_data_callback(data_callback)
    monitor.add_alert_callback(alert_callback)
    
    return monitor

if __name__ == "__main__":
    print("Live Spread Monitor Example")
    print("==========================")
    print("This example demonstrates real-time spread monitoring using WebSockets.")
    print("Note: This requires an active internet connection and will connect to Binance WebSocket.")
    print()
    
    try:
        # Create and start monitor
        monitor = create_live_dashboard_example()
        
        print("Starting live monitor... (Press Ctrl+C to stop)")
        monitor.start()
        
        # Run for a demo period
        time.sleep(60)  # Run for 1 minute
        
    except KeyboardInterrupt:
        print("\nStopping monitor...")
    finally:
        if 'monitor' in locals():
            monitor.stop()
    
    print("Example completed.")