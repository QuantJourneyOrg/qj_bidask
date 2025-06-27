import pytest
import numpy as np
import pandas as pd
from quantjourney_bidask import edge, edge_rolling

@pytest.fixture
def ohlc_data():
    """Test OHLC data for rolling edge estimation."""
    np.random.seed(42)
    n = 50
    base_price = 100
    
    # Generate realistic OHLC data
    prices = base_price + np.cumsum(np.random.normal(0, 0.5, n))
    
    return pd.DataFrame({
        'open': prices,
        'high': prices * (1 + np.random.uniform(0, 0.02, n)),
        'low': prices * (1 - np.random.uniform(0, 0.02, n)),
        'close': prices + np.random.normal(0, 0.2, n)
    })

@pytest.mark.parametrize("window", [3, 21, 100])
@pytest.mark.parametrize("sign", [True, False])
@pytest.mark.parametrize("step", [1, 5])
def test_edge_rolling(ohlc_data, window, sign, step):
    """Test edge_rolling against edge function for consistency."""
    rolling_estimates = edge_rolling(
        df=ohlc_data, window=window, sign=sign, step=step
    )
    assert isinstance(rolling_estimates, pd.Series)

    expected_estimates = []
    for t in range(0, len(ohlc_data), step):
        t1 = t + 1
        t0 = t1 - window
        estimate = edge(
            ohlc_data.open.values[t0:t1],
            ohlc_data.high.values[t0:t1],
            ohlc_data.low.values[t0:t1],
            ohlc_data.close.values[t0:t1],
            sign=sign
        ) if t0 >= 0 else np.nan
        expected_estimates.append(estimate)

    np.testing.assert_allclose(
        rolling_estimates.dropna(),
        [e for e in expected_estimates if not np.isnan(e)],
        rtol=1e-8,
        atol=1e-8,
        err_msg="Rolling estimates do not match expected estimates"
    )