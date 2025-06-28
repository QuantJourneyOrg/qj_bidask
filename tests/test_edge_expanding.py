"""
Unit tests for expanding window EDGE estimator.

Test suite for expanding window EDGE estimator with comprehensive validation
of expanding window behavior and accuracy.

Author: Jakub Polec
Date: 2025-06-28

Part of the QuantJourney framework - The framework with advanced quantitative 
finance tools and insights.
"""
import numpy as np
import pandas as pd
import pytest

from quantjourney_bidask import edge, edge_expanding


@pytest.fixture
def ohlc_data():
    """Test OHLC data for expanding edge estimation."""
    np.random.seed(42)
    n = 100
    base_price = 100
    prices = base_price + np.cumsum(np.random.normal(0, 0.3, n))
    return pd.DataFrame({
        "open": prices,
        "high": prices * (1 + np.random.uniform(0, 0.015, n)),
        "low": prices * (1 - np.random.uniform(0, 0.015, n)),
        "close": prices + np.random.normal(0, 0.15, n),
    })


@pytest.mark.parametrize("min_periods", [3, 21, 100])
@pytest.mark.parametrize("sign", [True, False])
def test_edge_expanding(ohlc_data, min_periods, sign):
    """Test edge_expanding against edge function for consistency."""
    expanding_estimates = edge_expanding(df=ohlc_data, min_periods=min_periods, sign=sign)
    assert isinstance(expanding_estimates, pd.Series)

    # --- THIS IS THE CORRECTED LOGIC ---
    expected_estimates_list = []
    for t in range(len(ohlc_data)):
        t1 = t + 1
        if t1 >= min_periods:
            estimate = edge(
                ohlc_data.open.values[:t1],
                ohlc_data.high.values[:t1],
                ohlc_data.low.values[:t1],
                ohlc_data.close.values[:t1],
                sign=sign,
            )
        else:
            estimate = np.nan
        expected_estimates_list.append(estimate)

    # Align both series and drop NaNs from both where either is NaN
    expected_series = pd.Series(expected_estimates_list, index=ohlc_data.index)
    comparison_df = pd.DataFrame({'actual': expanding_estimates, 'expected': expected_series}).dropna()

    np.testing.assert_allclose(
        comparison_df['actual'],
        comparison_df['expected'],
        rtol=1e-6, # Relaxed tolerance slightly for floating point differences
        atol=1e-6,
        err_msg="Expanding estimates do not match expected estimates",
    )