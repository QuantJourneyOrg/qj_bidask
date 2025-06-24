import math
import numpy as np
import pandas as pd
import pytest
from quantjourney_bidask import edge, edge_rolling, edge_expanding

def simulate_prices(n=100, spread=0.01, seed=42):
    """Simulate OHLC price data for testing, with a given true spread."""
    rng = np.random.default_rng(seed)
    mid = 100 * np.exp(np.cumsum(rng.normal(0, 0.01, size=n)))  # mid-price random walk
    opens = []; highs = []; lows = []; closes = []
    prev_close = mid[0]
    for t in range(n):
        # Open at previous close (for simplicity)
        o = prev_close
        # Simulate intraday extremes around mid
        intraday_up = rng.random() * 0.02
        intraday_down = rng.random() * 0.02
        mid_val = mid[t]
        high_mid = mid_val * (1 + intraday_up)
        low_mid = mid_val * (1 - intraday_down)
        # Determine high/low trades including spread
        high_trade = high_mid * (1 + spread/2)
        low_trade = low_mid * (1 - spread/2)
        # Randomize first and last trade (open and close)
        if rng.random() < 0.5:
            o_trade = mid_val * (1 + spread/2)
        else:
            o_trade = mid_val * (1 - spread/2)
        if rng.random() < 0.5:
            c_trade = mid_val * (1 + spread/2)
        else:
            c_trade = mid_val * (1 - spread/2)
        H = max(high_trade, o_trade, c_trade)
        L = min(low_trade, o_trade, c_trade)
        opens.append(o_trade); highs.append(H); lows.append(L); closes.append(c_trade)
        prev_close = c_trade
    df = pd.DataFrame({'open': opens, 'high': highs, 'low': lows, 'close': closes})
    return df

def test_edge_consistency():
    # Simulate a dataset and test consistency of estimators
    df = simulate_prices(n=50, spread=0.01)
    full_est = edge(df['open'], df['high'], df['low'], df['close'])
    # Expanding final value should match full_est (same data)
    exp_series = edge_expanding(df, min_periods=len(df))
    assert math.isclose(exp_series.iloc[-1], full_est, rel_tol=1e-6, abs_tol=1e-6)
    # Rolling with window = full length should also match full_est at end
    roll_series = edge_rolling(df, window=len(df))
    assert math.isclose(roll_series.iloc[-1], full_est, rel_tol=1e-6, abs_tol=1e-6)

def test_minimum_observations():
    # Provide a small dataset (3 points) where estimate is just defined
    prices = {'open':[100, 102, 101], 'high':[102, 103, 103], 'low':[99, 100, 100], 'close':[101, 101, 102]}
    df = pd.DataFrame(prices)
    est = edge(df['open'], df['high'], df['low'], df['close'])
    # Should produce a number (not NaN) since n=3 is the minimum
    assert not math.isnan(est)
    # With fewer than 3 points, result should be NaN
    df2 = df.iloc[:2]
    est2 = edge(df2['open'], df2['high'], df2['low'], df2['close'])
    assert math.isnan(est2)

def test_sign_parameter_behavior():
    # Construct a scenario likely to yield a very small or negative estimate
    # e.g., minimal price variation
    prices = {'open':[100, 100, 100], 'high':[100, 100, 100], 'low':[100, 100, 100], 'close':[100, 100, 100]}
    df = pd.DataFrame(prices)
    est_abs = edge(df['open'], df['high'], df['low'], df['close'], sign=False)
    est_signed = edge(df['open'], df['high'], df['low'], df['close'], sign=True)
    # In this degenerate case, both should be NaN (no variation to estimate)
    assert math.isnan(est_abs) and math.isnan(est_signed)
    # For a normal case, signed output should have same magnitude as unsigned
    df2 = simulate_prices(n=10, spread=0.005)
    val_abs = edge(df2['open'], df2['high'], df2['low'], df2['close'], sign=False)
    val_signed = edge(df2['open'], df2['high'], df2['low'], df2['close'], sign=True)
    if not math.isnan(val_signed):
        assert math.isclose(abs(val_signed), val_abs, rel_tol=1e-8)
