from .edge import edge
from .edge_rolling import edge_rolling
from .edge_expanding import edge_expanding

# Import version from package metadata
try:
    from importlib.metadata import version, metadata
    __version__ = version("quantjourney-bidask")
    _meta = metadata("quantjourney-bidask")
    __author__ = "Jakub Polec"
    __email__ = "jakub@quantjourney.pro"
    __license__ = "MIT"
except ImportError:
    # Fallback for development mode
    __version__ = "0.9.5"
    __author__ = "Jakub Polec"
    __email__ = "jakub@quantjourney.pro"
    __license__ = "MIT"

__all__ = ['edge', 'edge_rolling', 'edge_expanding']