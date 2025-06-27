import pytest
import pandas as pd
import asyncio
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data.fetch import DataFetcher, get_crypto_data, get_stock_data, stream_btc_data
from unittest.mock import patch, Mock

def test_data_fetcher_init():
    """Test DataFetcher initialization."""
    fetcher = DataFetcher()
    assert fetcher.data_dir == "data"
    
def test_crypto_data_synthetic():
    """Test crypto data fetching falls back to synthetic data."""
    async def test_crypto():
        df = await get_crypto_data("BTC/USDT", "binance", "1m", 10)
        return df
    
    df = asyncio.run(test_crypto())
    assert isinstance(df, pd.DataFrame)
    assert 'timestamp' in df.columns
    assert 'symbol' in df.columns
    assert 'open' in df.columns
    assert 'high' in df.columns
    assert 'low' in df.columns
    assert 'close' in df.columns
    assert 'volume' in df.columns
    assert len(df) == 10

def test_stock_data():
    """Test stock data fetcher."""
    df = get_stock_data("AAPL", "5d")
    
    assert isinstance(df, pd.DataFrame)
    if not df.empty:  # Only test structure if data is fetched
        assert 'timestamp' in df.columns
        assert 'symbol' in df.columns
        assert 'open' in df.columns
        assert 'high' in df.columns
        assert 'low' in df.columns
        assert 'close' in df.columns
        assert 'volume' in df.columns
        
def test_btc_websocket_synthetic():
    """Test BTC websocket data generation."""
    async def test_websocket():
        fetcher = DataFetcher()
        df = await fetcher.get_btc_1m_websocket(duration_seconds=5)
        return df
        
    df = asyncio.run(test_websocket())
    assert isinstance(df, pd.DataFrame)
    assert len(df) == 5
    assert 'timestamp' in df.columns
    assert 'symbol' in df.columns
    assert 'price' in df.columns
    assert 'volume' in df.columns
    assert 'bid' in df.columns
    assert 'ask' in df.columns
    assert 'spread' in df.columns

def test_stream_btc_data():
    """Test stream BTC data convenience function."""
    async def test_stream():
        return await stream_btc_data(duration_seconds=3)
        
    df = asyncio.run(test_stream())
    assert isinstance(df, pd.DataFrame)
    assert len(df) == 3
    assert 'symbol' in df.columns
    assert df['symbol'].iloc[0] == 'BTCUSDT'

def test_data_save_load():
    """Test data save and load functionality."""
    import tempfile
    import os
    
    # Create temporary directory for testing
    with tempfile.TemporaryDirectory() as temp_dir:
        fetcher = DataFetcher(data_dir=temp_dir)
        
        # Create test dataframe
        test_df = pd.DataFrame({
            'timestamp': pd.date_range('2024-01-01', periods=5, freq='D'),
            'symbol': ['TEST'] * 5,
            'open': [100, 101, 102, 103, 104],
            'high': [105, 106, 107, 108, 109],
            'low': [95, 96, 97, 98, 99],
            'close': [102, 103, 104, 105, 106],
            'volume': [1000, 1100, 1200, 1300, 1400]
        })
        
        # Test save
        filepath = fetcher.save_data(test_df, 'test_data.csv')
        assert os.path.exists(filepath)
        
        # Test load
        loaded_df = fetcher.load_data('test_data.csv')
        assert isinstance(loaded_df, pd.DataFrame)
        assert len(loaded_df) == 5
        assert list(loaded_df.columns) == list(test_df.columns)