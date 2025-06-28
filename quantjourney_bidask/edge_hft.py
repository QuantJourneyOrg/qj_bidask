"""
HFT-Optimized EDGE estimator for bid-ask spread calculation.

This version is hyper-optimized for maximum speed and is intended for
latency-sensitive applications like High-Frequency Trading.

It uses a targeted, fastmath-enabled Numba kernel for the lowest possible
execution time.

**WARNING:** This implementation uses `fastmath=True`, which prioritizes speed
over strict IEEE 754 compliance. It assumes the input data is **perfectly clean**
(contains no NaN or Inf values). Passing messy data may result in NaN output
where the standard `edge.py` version would produce a valid number. Use this
version only when you have a robust data sanitization pipeline upstream.

For general-purpose, robust estimation, use the standard `edge.py` module.

Author: Jakub Polec
Date: 2025-06-28
"""
import warnings
import numpy as np
from numba import jit, prange
from typing import Union, List, Any

# This is the targeted kernel. We add `fastmath=True` for an extra performance
# boost in this dense numerical section.
@jit(nopython=True, cache=True, fastmath=True)
def _compute_spread_numba_optimized(r1, r2, r3, r4, r5, tau, po, pc, pt):
    """
    Optimized core spread calculation using Numba with fastmath.
    This is the computational bottleneck and benefits most from JIT compilation.
    """
    # Numba is highly efficient with NumPy functions in nopython mode.
    d1 = r1 - np.nanmean(r1) / pt * tau     
    d3 = r3 - np.nanmean(r3) / pt * tau
    d5 = r5 - np.nanmean(r5) / pt * tau
    
    x1 = -4.0 / po * d1 * r2 + -4.0 / pc * d3 * r4
    x2 = -4.0 / po * d1 * r5 + -4.0 / pc * d5 * r4
    
    e1 = np.nanmean(x1)
    e2 = np.nanmean(x2)
    
    v1 = np.nanmean(x1**2) - e1**2
    v2 = np.nanmean(x2**2) - e2**2
    
    vt = v1 + v2
    s2 = (v2 * e1 + v1 * e2) / vt if vt > 0.0 else (e1 + e2) / 2.0
    
    return s2

def edge(
    open_prices: Union[List[float], Any],
    high: Union[List[float], Any],
    low: Union[List[float], Any],
    close: Union[List[float], Any],
    sign: bool = False,
    min_pt: float = 1e-6,
    debug: bool = False,
) -> float:
    """
    Estimate the effective bid-ask spread from OHLC prices.
    Public-facing function using the hybrid optimization strategy.
    """
    # --- 1. Input Validation and Conversion ---
    o_arr = np.asarray(open_prices, dtype=float)
    h_arr = np.asarray(high, dtype=float)
    l_arr = np.asarray(low, dtype=float)
    c_arr = np.asarray(close, dtype=float)

    nobs = len(o_arr)
    if not (len(h_arr) == nobs and len(l_arr) == nobs and len(c_arr) == nobs):
        raise ValueError("Input arrays must have the same length.")

    if nobs < 3:
        if debug: print("NaN reason: nobs < 3")
        return np.nan

    # --- 2. Log-Price Calculation (NumPy is fastest for this) ---
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", RuntimeWarning)
        o = np.log(np.where(o_arr > 0, o_arr, np.nan))
        h = np.log(np.where(h_arr > 0, h_arr, np.nan))
        l = np.log(np.where(l_arr > 0, l_arr, np.nan))
        c = np.log(np.where(c_arr > 0, c_arr, np.nan))
        m = (h + l) / 2.0

    # --- 3. Shift and Vectorized Calculations (NumPy is fastest for this) ---
    o_t, h_t, l_t, m_t = o[1:], h[1:], l[1:], m[1:]
    h_tm1, l_tm1, c_tm1, m_tm1 = h[:-1], l[:-1], c[:-1], m[:-1]

    r1 = m_t - o_t
    r2 = o_t - m_tm1
    r3 = m_t - c_tm1
    r4 = c_tm1 - m_tm1
    r5 = o_t - c_tm1

    tau = np.where(np.isnan(h_t) | np.isnan(l_t) | np.isnan(c_tm1), np.nan, ((h_t != l_t) | (l_t != c_tm1)).astype(float))
    po1 = tau * np.where(np.isnan(o_t) | np.isnan(h_t), np.nan, (o_t != h_t).astype(float))
    po2 = tau * np.where(np.isnan(o_t) | np.isnan(l_t), np.nan, (o_t != l_t).astype(float))
    pc1 = tau * np.where(np.isnan(c_tm1) | np.isnan(h_tm1), np.nan, (c_tm1 != h_tm1).astype(float))
    pc2 = tau * np.where(np.isnan(c_tm1) | np.isnan(l_tm1), np.nan, (c_tm1 != l_tm1).astype(float))
    
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", RuntimeWarning)
        pt = np.nanmean(tau)
        po = np.nanmean(po1) + np.nanmean(po2)
        pc = np.nanmean(pc1) + np.nanmean(pc2)

    # --- 4. Final Checks and Kernel Call ---
    if np.nansum(tau) < 2 or po == 0.0 or pc == 0.0 or pt < min_pt:
        if debug: print(f"NaN reason: Insufficient valid data (tau_sum={np.nansum(tau)}, po={po}, pc={pc}, pt={pt})")
        return np.nan

    # *** THE FIX: Call the correctly named JIT function ***
    s2 = _compute_spread_numba_optimized(r1, r2, r3, r4, r5, tau, po, pc, pt)
    
    if np.isnan(s2):
        return np.nan

    s = np.sqrt(np.abs(s2))
    if sign:
        s *= np.sign(s2)
        
    return float(s)