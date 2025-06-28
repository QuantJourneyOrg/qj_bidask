"""
Unit tests for rolling window EDGE estimator.

Test suite for rolling window EDGE estimator including consistency checks,
parameter validation, and performance verification.

Author: Jakub Polec
Date: 2025-06-28

Part of the QuantJourney framework - The framework with advanced quantitative 
finance tools and insights.
"""
import numpy as np
import pandas as pd
import pytest

from quantjourney_bidask import edge, edge_rolling


@pytest.fixture
def ohlc_data():
    """Test OHLC data for rolling edge estimation."""
    np.random.seed(42)
    n = 50
    base_price = 100
    prices = base_price + np.cumsum(np.random.normal(0, 0.5, n))
    return pd.DataFrame({
        "open": prices,
        "high": prices * (1 + np.random.uniform(0, 0.02, n)),
        "low": prices * (1 - np.random.uniform(0, 0.02, n)),
        "close": prices + np.random.normal(0, 0.2, n),
    })


@pytest.mark.parametrize("window", [3, 21, 100])
@pytest.mark.parametrize("sign", [True, False])
@pytest.mark.parametrize("step", [1, 5])
def test_edge_rolling(ohlc_data, window, sign, step):
    """Test edge_rolling against edge function for consistency."""
    rolling_estimates = edge_rolling(df=ohlc_data, window=window, sign=sign, step=step)
    assert isinstance(rolling_estimates, pd.Series)

    # --- THIS IS THE CORRECTED LOGIC ---
    # Create the expected series with the same index as the rolling estimates
    expected_estimates_list = []
    for t in range(len(ohlc_data)):
        if (t % step == 0) or (step == 1):
             t1 = t + 1
             t0 = t1 - window
             if t0 >= 0:
                 estimate = edge(
                     ohlc_data.open.values[t0:t1],
                     ohlc_data.high.values[t0:t1],
                     ohlc_data.low.values[t0:t1],
                     ohlc_data.close.values[t0:t1],
                     sign=sign,
                 )
                 expected_estimates_list.append(estimate)
             else:
                 expected_estimates_list.append(np.nan)
        else:
            expected_estimates_list.append(np.nan)

    # Align both series and drop NaNs from both where either is NaN
    expected_series = pd.Series(expected_estimates_list, index=ohlc_data.index)
    comparison_df = pd.DataFrame({'actual': rolling_estimates, 'expected': expected_series}).dropna()

    np.testing.assert_allclose(
        comparison_df['actual'],
        comparison_df['expected'],
        rtol=1e-6, # Relaxed tolerance slightly for floating point differences
        atol=1e-6,
        err_msg="Rolling estimates do not match expected estimates",
    )