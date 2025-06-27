import pytest
import numpy as np
import pandas as pd
from quantjourney_bidask import edge, edge_expanding

@pytest.fixture
def ohlc_data():
    """Test OHLC data for expanding edge estimation."""
    np.random.seed(42)
    n = 100  # Larger dataset for expanding window tests
    base_price = 100
    
    # Generate realistic OHLC data
    prices = base_price + np.cumsum(np.random.normal(0, 0.3, n))
    
    return pd.DataFrame({
        'open': prices,
        'high': prices * (1 + np.random.uniform(0, 0.015, n)),
        'low': prices * (1 - np.random.uniform(0, 0.015, n)),
        'close': prices + np.random.normal(0, 0.15, n)
    })

@pytest.mark.parametrize("min_periods", [3, 21, 100])
@pytest.mark.parametrize("sign", [True, False])
def test_edge_expanding(ohlc_data, min_periods, sign):
    """Test edge_expanding against edge function for consistency."""
    expanding_estimates = edge_expanding(
        df=ohlc_data, min_periods=min_periods, sign=sign
    )
    assert isinstance(expanding_estimates, pd.Series)

    expected_estimates = []
    for t in range(len(ohlc_data)):
        t1 = t + 1
        estimate = edge(
            ohlc_data.open.values[:t1],
            ohlc_data.high.values[:t1],
            ohlc_data.low.values[:t1],
            ohlc_data.close.values[:t1],
            sign=sign
        ) if t1 >= min_periods else np.nan
        expected_estimates.append(estimate)

    np.testing.assert_allclose(
        expanding_estimates.dropna(),
        [e for e in expected_estimates if not np.isnan(e)],
        rtol=1e-8,
        atol=1e-8,
        err_msg="Expanding estimates do not match expected estimates"
    )