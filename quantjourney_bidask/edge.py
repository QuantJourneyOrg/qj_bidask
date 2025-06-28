"""
Optimized and robust EDGE estimator for bid-ask spread calculation.

Implements the efficient estimator from Ardia, Guidotti, & Kroencke (2024) for
single-period bid-ask spread estimation from OHLC prices. This version is
optimized for speed using Numba and careful memory handling, while ensuring
numerical identity with the reference implementation.

Author: Jakub Polec
Date: 2025-06-28
"""
import warnings
from typing import Union, List, Any
import numpy as np
from numba import jit

@jit(nopython=True, cache=True)
def _compute_spread_numba(r1, r2, r3, r4, r5, tau, po, pc, pt):
    """
    Core spread calculation using Numba for maximum performance.
    This is the computational bottleneck and benefits most from JIT compilation.
    """
    # De-mean returns, scaling by the probability of a valid period (pt)
    # This aligns with the GMM framework where moments are conditioned on tau=1
    r1_mean = np.nanmean(r1)    # Mean of the first return
    r3_mean = np.nanmean(r3)    # Mean of the third return
    r5_mean = np.nanmean(r5)    # Mean of the fifth return
    
    d1 = r1 - r1_mean / pt * tau     # De-mean returns, scaling by the probability of a valid period (pt)
    d3 = r3 - r3_mean / pt * tau     # De-mean returns, scaling by the probability of a valid period (pt)
    d5 = r5 - r5_mean / pt * tau     # De-mean returns, scaling by the probability of a valid period (pt)
    
    # GMM moment conditions
    x1 = -4.0 / po * d1 * r2 + -4.0 / pc * d3 * r4     # First moment condition
    x2 = -4.0 / po * d1 * r5 + -4.0 / pc * d5 * r4     # Second moment condition
    
    # Expectations of the moment conditions
    e1 = np.nanmean(x1)     # Expectation of the first moment condition
    e2 = np.nanmean(x2)     # Expectation of the second moment condition
    
    # Variances for optimal weighting
    v1 = np.nanmean(x1**2) - e1**2     # Variance of the first moment condition
    v2 = np.nanmean(x2**2) - e2**2     # Variance of the second moment condition
    
    # Optimal GMM weighting
    vt = v1 + v2     # Total variance
    # If total variance is zero or negative (rare small sample issue), use simple average
    s2 = (v2 * e1 + v1 * e2) / vt if vt > 0.0 else (e1 + e2) / 2.0     # Spread estimate
    
    return s2

def edge(
    open_prices: Union[List[float], Any],
    high: Union[List[float], Any],
    low: Union[List[float], Any],
    close: Union[List[float], Any],
    sign: bool = False,
    min_pt: float = 1e-6, # Keep this robustness check
    debug: bool = False,
) -> float:
    """
    Estimate the effective bid-ask spread from OHLC prices.

    Implements the efficient estimator described in Ardia, Guidotti, & Kroencke
    (2024): https://doi.org/10.1016/j.jfineco.2024.103916.

    Args:
        open_prices : array-like
            Vector of open prices.
        high : array-like
            Vector of high prices.
        low : array-like
            Vector of low prices.
        close : array-like
            Vector of close prices.
        sign : bool, default False
            If True, returns signed estimates. If False, returns absolute values.
        min_pt : float, default 1e-6
            Minimum probability threshold for tau to ensure reliable estimates.
        debug : bool, default False
            If True, prints intermediate values.

    Returns:
        float
            Estimated bid-ask spread. Returns np.nan if invalid.

    Examples:
        >>> import numpy as np
        >>> from edge import edge
        >>> open_prices = np.array([100.0, 101.5, 99.8, 102.1, 100.9])
        >>> high = np.array([102.3, 103.0, 101.2, 103.5, 102.0])
        >>> low = np.array([99.5, 100.8, 98.9, 101.0, 100.1])
        >>> close = np.array([101.2, 102.5, 100.3, 102.8, 101.5])
    """
    # --- 1. Input Validation and Conversion ---
    o_arr = np.asarray(open_prices, dtype=float)    # Convert to numpy array
    h_arr = np.asarray(high, dtype=float)           # Convert to numpy array
    l_arr = np.asarray(low, dtype=float)            # Convert to numpy array
    c_arr = np.asarray(close, dtype=float)          # Convert to numpy array

    nobs = len(o_arr)
    if not (len(h_arr) == nobs and len(l_arr) == nobs and len(c_arr) == nobs):
        raise ValueError("Input arrays must have the same length.")

    if nobs < 3:    # If there are less than 3 observations, return NaN
        if debug: print("NaN reason: nobs < 3")
        return np.nan

    # --- 2. Log-Price Calculation ---
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", RuntimeWarning)
        # Replace non-positive prices with NaN to avoid log(0) or log(-1) issues
        o = np.log(np.where(o_arr > 0, o_arr, np.nan))  # Log-price of the open price
        h = np.log(np.where(h_arr > 0, h_arr, np.nan))  # Log-price of the high price
        l = np.log(np.where(l_arr > 0, l_arr, np.nan))  # Log-price of the low price
        c = np.log(np.where(c_arr > 0, c_arr, np.nan))  # Log-price of the close price
        m = (h + l) / 2.0     # Mid-price log

    # --- 3. Shift Arrays for Lagged Calculations (THE CRITICAL FIX) ---
    # All calculations from here on use N-1 observations.
    o_t = o[1:] # Open price at time t
    h_t = h[1:] # High price at time t
    l_t = l[1:] # Low price at time t
    m_t = m[1:] # Mid-price at time t
    
    h_tm1 = h[:-1] # High price at time t-1
    l_tm1 = l[:-1]
    c_tm1 = c[:-1]
    m_tm1 = m[:-1]

    # --- 4. Compute Log-Returns ---
    r1 = m_t - o_t          # Mid-price - Open price
    r2 = o_t - m_tm1        # Open price - Previous mid-price
    r3 = m_t - c_tm1        # Mid-price - Previous close
    r4 = c_tm1 - m_tm1      # Previous close - Previous mid-price
    r5 = o_t - c_tm1        # Open price - Previous close

    # --- 5. Compute Indicator Variables ---
    tau = np.where(np.isnan(h_t) | np.isnan(l_t) | np.isnan(c_tm1), np.nan, ((h_t != l_t) | (l_t != c_tm1)).astype(float))
    po1 = tau * np.where(np.isnan(o_t) | np.isnan(h_t), np.nan, (o_t != h_t).astype(float))
    po2 = tau * np.where(np.isnan(o_t) | np.isnan(l_t), np.nan, (o_t != l_t).astype(float))
    pc1 = tau * np.where(np.isnan(c_tm1) | np.isnan(h_tm1), np.nan, (c_tm1 != h_tm1).astype(float))
    pc2 = tau * np.where(np.isnan(c_tm1) | np.isnan(l_tm1), np.nan, (c_tm1 != l_tm1).astype(float))
    
    # --- 6. Compute Probabilities ---
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", RuntimeWarning)
        pt = np.nanmean(tau)                        # Probability of a valid period
        po = np.nanmean(po1) + np.nanmean(po2)      # Probability of open price not equal to high
        pc = np.nanmean(pc1) + np.nanmean(pc2)      # Probability of close price not equal to high

    if debug:
        print(f"Debug: tau_sum={np.nansum(tau):.2f}, po={po:.4f}, pc={pc:.4f}, pt={pt:.4f}")

    # --- 7. Check for Data Quality ---
    if np.nansum(tau) < 2 or po == 0.0 or pc == 0.0 or pt < min_pt:
        if debug: print(f"NaN reason: Insufficient valid data (tau_sum={np.nansum(tau)}, po={po}, pc={pc}, pt={pt})")
        return np.nan

    # --- 8. Compute Spread (using the Numba-optimized function) ---
    s2 = _compute_spread_numba(r1, r2, r3, r4, r5, tau, po, pc, pt) # Spread estimate
    
    if np.isnan(s2):
        if debug: print("NaN reason: s2 calculation resulted in NaN")
        return np.nan

    s = np.sqrt(np.abs(s2))
    if sign:
        s *= np.sign(s2)     # Signed spread estimate
        
    if debug:
        print(f"Debug: s2={s2:.6e}, s={s:.6e}")

    return float(s)