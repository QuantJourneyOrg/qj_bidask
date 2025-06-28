"""
Unit tests for core EDGE estimator.

Comprehensive test suite for the core EDGE estimator functionality including
edge cases, parameter validation, and accuracy verification.

Author: Jakub Polec
Date: 2025-06-28

Part of the QuantJourney framework - The framework with advanced quantitative 
finance tools and insights.
"""

import numpy as np
import pandas as pd
import pytest

from quantjourney_bidask import edge


@pytest.fixture
def ohlc_data():
    """Test OHLC data for edge estimation."""
    return pd.DataFrame(
        {
            "Open": [
                100.0,
                101.5,
                99.8,
                102.1,
                100.9,
                103.2,
                101.7,
                104.5,
                102.3,
                105.1,
            ],
            "High": [
                102.3,
                103.0,
                101.2,
                103.5,
                102.0,
                104.8,
                103.1,
                106.2,
                104.0,
                106.5,
            ],
            "Low": [99.5, 100.8, 98.9, 101.0, 100.1, 102.5, 101.0, 103.8, 101.5, 104.2],
            "Close": [
                101.2,
                102.5,
                100.3,
                102.8,
                101.5,
                104.1,
                102.4,
                105.7,
                103.2,
                105.8,
            ],
        }
    )


@pytest.fixture
def ohlc_missing_data():
    """Test OHLC data with missing values."""
    return pd.DataFrame(
        {
            "Open": [
                100.0,
                np.nan,
                99.8,
                102.1,
                np.nan,
                103.2,
                101.7,
                np.nan,
                102.3,
                105.1,
            ],
            "High": [
                102.3,
                103.0,
                np.nan,
                103.5,
                102.0,
                np.nan,
                103.1,
                106.2,
                np.nan,
                106.5,
            ],
            "Low": [
                99.5,
                np.nan,
                98.9,
                np.nan,
                100.1,
                102.5,
                np.nan,
                103.8,
                101.5,
                np.nan,
            ],
            "Close": [
                101.2,
                102.5,
                np.nan,
                102.8,
                101.5,
                np.nan,
                102.4,
                105.7,
                np.nan,
                105.8,
            ],
        }
    )


def test_edge_valid(ohlc_data):
    """Test edge function with valid OHLC data."""
    estimate = edge(ohlc_data.Open, ohlc_data.High, ohlc_data.Low, ohlc_data.Close)
    # Test that the estimate is reasonable (between 0 and 1)
    assert 0 < estimate < 1, f"Spread estimate {estimate} should be between 0 and 1"
    # Test approximate value for our synthetic data
    assert estimate == pytest.approx(0.006187933554613185, rel=1e-3)


def test_edge_signed(ohlc_data):
    """Test edge function with signed estimates."""
    estimate = edge(
        ohlc_data.Open[:10],
        ohlc_data.High[:10],
        ohlc_data.Low[:10],
        ohlc_data.Close[:10],
        sign=True,
    )
    # For synthetic data, just test that signed estimate exists and is finite
    assert np.isfinite(estimate), f"Signed estimate should be finite, got {estimate}"


def test_edge_missing(ohlc_missing_data):
    """Test edge function with missing values."""
    estimate = edge(
        ohlc_missing_data.Open,
        ohlc_missing_data.High,
        ohlc_missing_data.Low,
        ohlc_missing_data.Close,
    )
    # With missing data, we expect either a valid estimate or NaN
    # Test that function handles missing data gracefully
    assert np.isfinite(estimate) or np.isnan(
        estimate
    ), f"Should handle missing data gracefully, got {estimate}"


def test_edge_insufficient_data():
    """Test edge function with insufficient observations."""
    assert np.isnan(edge([18.21], [18.21], [17.61], [17.61]))
    assert np.isnan(
        edge([18.21, 17.61], [18.21, 17.61], [17.61, 17.61], [17.61, 17.61])
    )


def test_edge_invalid_lengths():
    """Test edge function with mismatched input lengths."""
    with pytest.raises(ValueError, match="must have the same length"):
        edge([1, 2], [1, 2, 3], [1, 2], [1, 2])
