import pytest
import numpy as np
import pandas as pd
from quantjourney_bidask import edge

@pytest.fixture
def ohlc_data():
    return pd.read_csv(
        "https://raw.githubusercontent.com/eguidotti/bidask/main/pseudocode/ohlc.csv"
    )

@pytest.fixture
def ohlc_missing_data():
    return pd.read_csv(
        "https://raw.githubusercontent.com/eguidotti/bidask/main/pseudocode/ohlc-miss.csv"
    )

def test_edge_valid(ohlc_data):
    """Test edge function with valid OHLC data."""
    estimate = edge(ohlc_data.Open, ohlc_data.High, ohlc_data.Low, ohlc_data.Close)
    assert estimate == pytest.approx(0.0101849034905478, rel=1e-6)

def test_edge_signed(ohlc_data):
    """Test edge function with signed estimates."""
    estimate = edge(
        ohlc_data.Open[:10], ohlc_data.High[:10], ohlc_data.Low[:10], ohlc_data.Close[:10],
        sign=True
    )
    assert estimate == pytest.approx(-0.016889917516422, rel=1e-6)

def test_edge_missing(ohlc_missing_data):
    """Test edge function with missing values."""
    estimate = edge(
        ohlc_missing_data.Open, ohlc_missing_data.High,
        ohlc_missing_data.Low, ohlc_missing_data.Close
    )
    assert estimate == pytest.approx(0.01013284969780197, rel=1e-6)

def test_edge_insufficient_data():
    """Test edge function with insufficient observations."""
    assert np.isnan(edge([18.21], [18.21], [17.61], [17.61]))
    assert np.isnan(edge(
        [18.21, 17.61], [18.21, 17.61], [17.61, 17.61], [17.61, 17.61]
    ))

def test_edge_invalid_lengths():
    """Test edge function with mismatched input lengths."""
    with pytest.raises(ValueError, match="must have the same length"):
        edge([1, 2], [1, 2, 3], [1, 2], [1, 2])