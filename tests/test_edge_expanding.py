import pytest
import numpy as np
import pandas as pd
from quantjourney_bidask import edge, edge_expanding

@pytest.fixture
def ohlc_data():
    return pd.read_csv(
        "https://raw.githubusercontent.com/eguidotti/bidask/main/pseudocode/ohlc.csv"
    )

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
            ohlc_data.Open.values[:t1],
            ohlc_data.High.values[:t1],
            ohlc_data.Low.values[:t1],
            ohlc_data.Close.values[:t1],
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