import pytest
import numpy as np
import pandas as pd
from quantjourney_bidask import edge, edge_rolling

@pytest.fixture
def ohlc_data():
    return pd.read_csv(
        "https://raw.githubusercontent.com/eguidotti/bidask/main/pseudocode/ohlc.csv"
    )

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
            ohlc_data.Open.values[t0:t1],
            ohlc_data.High.values[t0:t1],
            ohlc_data.Low.values[t0:t1],
            ohlc_data.Close.values[t0:t1],
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