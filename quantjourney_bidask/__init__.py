"""
QuantJourney Bid-Ask Spread Estimator - Core Library.

Efficient estimation of bid-ask spreads from OHLC prices using the methodology
from Ardia, Guidotti, & Kroencke (2024).

Author: Jakub Polec  
Date: 2025-06-28

Part of the QuantJourney framework - The framework with advanced quantitative 
finance tools and insights.
"""

from .edge import edge
from .edge_expanding import edge_expanding
from .edge_rolling import edge_rolling

# Import version from package metadata
try:
    from importlib.metadata import metadata, version

    __version__ = version("quantjourney-bidask")
    _meta = metadata("quantjourney-bidask")
    __author__ = "Jakub Polec"
    __email__ = "jakub@quantjourney.pro"
    __license__ = "MIT"
except ImportError:
    # Fallback for development mode
    __version__ = "X.Y"
    __author__ = "Jakub Polec"
    __email__ = "jakub@quantjourney.pro"
    __license__ = "MIT"

__all__ = ["edge", "edge_rolling", "edge_expanding"]
