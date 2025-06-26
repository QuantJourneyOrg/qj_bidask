import pytest
import pandas as pd
from data.fetch import fetch_binance_data, fetch_yfinance_data
from unittest.mock import patch, Mock

@patch('requests.post')
@patch('requests.get')
def test_fetch_binance_data(mock_get, mock_post):
    """Test Binance data fetcher with mocked API responses."""
    # Mock fetch response
    mock_post.return_value = Mock(status_code=200, json=lambda: {"task_id": "test123"})
    
    # Mock task status
    mock_get.return_value = Mock(
        status_code=200,
        json=lambda: {
            "status": "ok",
            "task": {"status": "completed", "message": "Task completed"}
        }
    )
    
    # Mock data query
    mock_post.side_effect = [
        Mock(status_code=200, json=lambda: {"task_id": "test123"}),
        Mock(status_code=200, json=lambda: {
            "data": [{
                "timestamp": "2024-01-01T00:00:00Z",
                "open": 40000.0,
                "high": 41000.0,
                "low": 39000.0,
                "close": 40500.0,
                "volume": 100.0
            }]
        })
    ]

    df = fetch_binance_data(
        symbols=["BTCUSDT"],
        timeframe="1m",
        start="2024-01-01T00:00:00Z",
        end="2024-01-01T01:00:00Z",
        api_key="test_key"
    )
    
    assert isinstance(df, pd.DataFrame)
    assert list(df.columns) == ['timestamp', 'symbol', 'open', 'high', 'low', 'close', 'volume']
    assert len(df) == 1
    assert df['symbol'].iloc[0] == "BTCUSDT"

def test_fetch_yfinance_data():
    """Test yfinance data fetcher."""
    df = fetch_yfinance_data(
        tickers=["AAPL"],
        period="5d",
        interval="1d"
    )
    
    assert isinstance(df, pd.DataFrame)
    assert list(df.columns) == ['timestamp', 'symbol', 'open', 'high', 'low', 'close', 'volume']
    assert df['symbol'].iloc[0] == "AAPL"
    assert len(df) > 0