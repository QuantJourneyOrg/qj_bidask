"""
quantjourney_bidask: Efficient bid-ask spread estimator from OHLC data.

Implements the efficient estimator (EDGE) of bid-ask spreads from open, high, low, and close prices 
as described in Ardia, Guidotti & Kroencke (2024):contentReference[oaicite:0]{index=0}. 
"""
__version__ = "0.1.0"

from quantjourney_bidask.edge import edge
from quantjourney_bidask.edge_rolling import edge_rolling
from quantjourney_bidask.edge_expanding import edge_expanding
from quantjourney_bidask.data_fetcher import fetch_binance_data, fetch_yfinance_data

__all__ = ['edge', 'edge_rolling', 'edge_expanding', 'fetch_binance_data', 'fetch_yfinance_data']
