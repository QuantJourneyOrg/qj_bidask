import numpy as np
import warnings
from typing import Union, List, Tuple, Any

def edge(
    open: Union[List[float], Any],
    high: Union[List[float], Any],
    low: Union[List[float], Any],
    close: Union[List[float], Any],
    sign: bool = False
) -> float:
    """
    Estimate the effective bid-ask spread from open, high, low, and close (OHLC) prices.

    Implements the efficient estimator described in Ardia, Guidotti, & Kroencke (2024):
    https://doi.org/10.1016/j.jfineco.2024.103916. The estimator computes the root mean square
    effective spread within the sample period using log-returns and indicator variables.

    Parameters
    ----------
    open : array-like
        Vector of open prices, sorted in ascending order of timestamp.
    high : array-like
        Vector of high prices, sorted in ascending order of timestamp.
    low : array-like
        Vector of low prices, sorted in ascending order of timestamp.
    close : array-like
        Vector of close prices, sorted in ascending order of timestamp.
    sign : bool, default False
        If True, returns signed estimates (negative values possible). If False, returns
        absolute values to reduce small-sample bias in averaging or regression studies.

    Returns
    -------
    float
        Estimated bid-ask spread as a fraction of price (e.g., 0.01 = 1% spread).
        Returns np.nan if the estimate cannot be computed (e.g., insufficient data).

    Notes
    -----
    - Requires at least 3 observations for a valid estimate.
    - Handles missing values (NaNs) automatically by excluding them from calculations.
    - The estimator assumes prices are positive and non-zero to compute log-prices.
    - For optimal results, use high-frequency data (e.g., minute or hourly) for frequently
      traded assets, or lower frequency (e.g., daily) for less liquid assets.

    Examples
    --------
    >>> import pandas as pd
    >>> # Example OHLC data
    >>> open_prices = [100.0, 101.5, 99.8, 102.1, 100.9]
    >>> high_prices = [102.3, 103.0, 101.2, 103.5, 102.0]
    >>> low_prices = [99.5, 100.8, 98.9, 101.0, 100.1]
    >>> close_prices = [101.2, 102.5, 100.3, 102.8, 101.5]
    >>> spread = edge(open_prices, high_prices, low_prices, close_prices)
    >>> print(f"Estimated spread: {spread:.6f}")
    Estimated spread: 0.007109
    """
    # Convert inputs to numpy arrays
    open = np.asarray(open, dtype=float)
    high = np.asarray(high, dtype=float)
    low = np.asarray(low, dtype=float)
    close = np.asarray(close, dtype=float)

    # Validate input lengths
    nobs = len(open)
    if len(high) != nobs or len(low) != nobs or len(close) != nobs:
        raise ValueError("Open, high, low, and close must have the same length")

    # Return NaN if insufficient observations
    if nobs < 3:
        return np.nan

    # Compute log-prices, handling non-positive prices
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", RuntimeWarning)
        o = np.log(np.where(open > 0, open, np.nan))
        h = np.log(np.where(high > 0, high, np.nan))
        l = np.log(np.where(low > 0, low, np.nan))
        c = np.log(np.where(close > 0, close, np.nan))
        m = (h + l) / 2.0  # Mid-price log

    # Shift log-prices by one period
    h1, l1, c1, m1 = h[:-1], l[:-1], c[:-1], m[:-1]
    o, h, l, c, m = o[1:], h[1:], l[1:], c[1:], m[1:]

    # Compute log-returns
    r1 = m - o        # Mid - Open
    r2 = o - m1       # Open - Previous Mid
    r3 = m - c1       # Mid - Previous Close
    r4 = c1 - m1      # Previous Close - Previous Mid
    r5 = o - c1       # Open - Previous Close

    # Compute indicator variables
    # tau: Indicator for valid price variation (1 if high != low or low != previous close)
    tau = np.where(np.isnan(h) | np.isnan(l) | np.isnan(c1), np.nan,
                   ((h != l) | (l != c1)).astype(float))
    
    # po1: Indicator for open price not equal to high, scaled by tau
    po1 = tau * np.where(np.isnan(o) | np.isnan(h), np.nan, (o != h).astype(float))
    
    # po2: Indicator for open price not equal to low, scaled by tau 
    po2 = tau * np.where(np.isnan(o) | np.isnan(l), np.nan, (o != l).astype(float))
    
    # pc1: Indicator for previous close not equal to previous high, scaled by tau
    pc1 = tau * np.where(np.isnan(c1) | np.isnan(h1), np.nan, (c1 != h1).astype(float))
    
    # pc2: Indicator for previous close not equal to previous low, scaled by tau
    pc2 = tau * np.where(np.isnan(c1) | np.isnan(l1), np.nan, (c1 != l1).astype(float))

    # Compute probabilities with NaN handling
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", RuntimeWarning)
        pt = np.nanmean(tau)
        po = np.nanmean(po1) + np.nanmean(po2)
        pc = np.nanmean(pc1) + np.nanmean(pc2)

    # Return NaN if insufficient valid periods or probabilities are zero
    if np.nansum(tau) < 2 or po == 0 or pc == 0:
        return np.nan

    # Compute de-meaned log-returns
    d1 = r1 - np.nanmean(r1) / pt * tau
    d3 = r3 - np.nanmean(r3) / pt * tau
    d5 = r5 - np.nanmean(r5) / pt * tau

    # Compute input vectors for GMM estimation
    # x1: First moment condition combining open-high-low and close-high-low effects
    x1 = -4.0 / po * d1 * r2 + -4.0 / pc * d3 * r4  # Scaled by probability of open/close extremes
    # x2: Second moment condition combining open-high-low-close and close-high-low-open effects
    x2 = -4.0 / po * d1 * r5 + -4.0 / pc * d5 * r4

    # Compute expectations (means) of the moment conditions
    e1 = np.nanmean(x1)  # First moment expectation
    e2 = np.nanmean(x2)  # Second moment expectation

    # Compute variances of the moment conditions for optimal weighting
    v1 = np.nanmean(x1**2) - e1**2  # Variance of first moment
    v2 = np.nanmean(x2**2) - e2**2  # Variance of second moment

    # Compute squared spread estimate using optimal GMM weights
    vt = v1 + v2  # Total variance for weighting
    # If total variance is positive, use optimal weighted average
    # Otherwise fall back to simple average of the two estimates
    s2 = (v2 * e1 + v1 * e2) / vt if vt > 0 else (e1 + e2) / 2.0

    # Compute signed root
    s = np.sqrt(np.abs(s2))
    if sign:
        s *= np.sign(s2)

    return float(s)