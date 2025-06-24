import pandas as pd
import requests
import yfinance as yf
from typing import Optional, List
from datetime import datetime

def fetch_binance_data(
    symbols: List[str],
    timeframe: str,
    start: str,
    end: str,
    api_key: str,
    api_url: str = "http://localhost:8000"
) -> pd.DataFrame:
    """
    Fetch OHLCV data from Binance using the provided FastAPI server.

    Parameters
    ----------
    symbols : List[str]
        List of trading pairs (e.g., ["BTCUSDT", "ETHUSDT"]).
    timeframe : str
        Data timeframe (e.g., "1m", "1h", "1d").
    start : str
        Start time in ISO 8601 format (e.g., "2024-01-01T00:00:00Z").
    end : str
        End time in ISO 8601 format (e.g., "2024-01-02T00:00:00Z").
    api_key : str
        API key for authentication.
    api_url : str, default "http://localhost:8000"
        Base URL of the FastAPI server.

    Returns
    -------
    pd.DataFrame
        DataFrame with columns ['open', 'high', 'low', 'close', 'volume', 'timestamp', 'symbol'].

    Raises
    ------
    ValueError
        If the API request fails or returns an error.
    """
    payload = {
        "exchange": "binance",
        "symbols": symbols,
        "start": start,
        "end": end,
        "timeframe": timeframe,
        "upload_d1": False,
        "force": False
    }
    headers = {"X-API-Key": api_key}
    
    # Initiate fetch request
    response = requests.post(f"{api_url}/fetch", json=payload, headers=headers)
    if response.status_code != 200:
        raise ValueError(f"Fetch request failed: {response.text}")
    
    task_id = response.json().get("task_id")
    if not task_id:
        raise ValueError("No task ID returned from fetch request")

    # Poll task status
    while True:
        status_response = requests.get(f"{api_url}/tasks/{task_id}")
        if status_response.status_code != 200:
            raise ValueError(f"Task status check failed: {status_response.text}")
        
        task = status_response.json().get("task")
        if task["status"] in ["completed", "failed"]:
            if task["status"] == "failed":
                raise ValueError(f"Task failed: {task.get('message')}")
            break

    # Query data
    data = []
    for symbol in symbols:
        query_payload = {
            "symbol": symbol,
            "timeframe": timeframe,
            "start": start,
            "end": end
        }
        query_response = requests.post(f"{api_url}/d1/query", json=query_payload)
        if query_response.status_code != 200:
            raise ValueError(f"Data query failed for {symbol}: {query_response.text}")
        
        rows = query_response.json().get("data", [])
        df = pd.DataFrame(rows)
        if not df.empty:
            df['symbol'] = symbol
            data.append(df)
    
    if not data:
        raise ValueError("No data retrieved for the specified parameters")
    
    result = pd.concat(data, ignore_index=True)
    result['timestamp'] = pd.to_datetime(result['timestamp'])
    return result[['timestamp', 'symbol', 'open', 'high', 'low', 'close', 'volume']]

def fetch_yfinance_data(
    tickers: List[str],
    period: str = "1mo",
    interval: str = "1d",
    start: Optional[str] = None,
    end: Optional[str] = None
) -> pd.DataFrame:
    """
    Fetch OHLCV data from Yahoo Finance using yfinance.

    Parameters
    ----------
    tickers : List[str]
        List of ticker symbols (e.g., ["AAPL", "MSFT"]).
    period : str, default "1mo"
        Data period (e.g., "1d", "1mo", "1y"). Ignored if start and end are provided.
    interval : str, default "1d"
        Data interval (e.g., "1m", "1h", "1d").
    start : str, optional
        Start date (e.g., "2024-01-01"). Overrides period if provided.
    end : str, optional
        End date (e.g., "2024-01-31"). Overrides period if provided.

    Returns
    -------
    pd.DataFrame
        DataFrame with columns ['open', 'high', 'low', 'close', 'volume', 'timestamp', 'symbol'].

    Raises
    ------
    ValueError
        If no data is retrieved for the specified parameters.
    """
    data = []
    for ticker in tickers:
        stock = yf.Ticker(ticker)
        if start and end:
            df = stock.history(start=start, end=end, interval=interval)
        else:
            df = stock.history(period=period, interval=interval)
        
        if df.empty:
            continue
        
        df = df.reset_index()
        df['symbol'] = ticker
        df = df.rename(columns={
            'Date': 'timestamp',
            'Open': 'open',
            'High': 'high',
            'Low': 'low',
            'Close': 'close',
            'Volume': 'volume'
        })
        data.append(df[['timestamp', 'symbol', 'open', 'high', 'low', 'close', 'volume']])
    
    if not data:
        raise ValueError("No data retrieved for the specified parameters")
    
    return pd.concat(data, ignore_index=True)