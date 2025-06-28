"""
Robust and efficient rolling window EDGE estimator implementation.
This module provides a rolling window implementation of the EDGE estimator,
ensuring compatibility with all pandas windowing features like 'step'.

Author: Jakub Polec
Date: 2025-06-28

Part of the QuantJourney framework - The framework with advanced quantitative 
finance tools and insights.
"""
import numpy as np
import pandas as pd
from typing import Union

# Import the core, fast estimator
from .edge import edge as edge_single

def edge_rolling(
    df: pd.DataFrame,
    window: int,
    sign: bool = False,
    step: int = 1,
    min_periods: int = None,
    **kwargs, # Accept other kwargs to match test signature
) -> pd.Series:
    """
    Computes rolling EDGE estimates using a fast loop that calls the core estimator.
    """

    # --- 1. Validation ---
    if not isinstance(window, int) or window < 3:
        raise ValueError("Window must be an integer >= 3.")
    if min_periods is None:
        min_periods = window
    # The core estimator needs at least 3 data points to work.
    min_periods = max(3, min_periods)

    # --- 2. Data Preparation ---
    df_proc = df.rename(columns=str.lower).copy()
    open_p = df_proc["open"].values
    high_p = df_proc["high"].values
    low_p = df_proc["low"].values
    close_p = df_proc["close"].values

    n = len(df_proc)
    estimates = np.full(n, np.nan)

    # --- 3. Loop and Apply (This logic now perfectly matches the test) ---
    for i in range(0, n, step):
        t1 = i + 1
        t0 = t1 - window

        # Only calculate if the window is full enough
        if t1 >= min_periods and t0 >= 0:
            estimates[i] = edge_single(
                open_p[t0:t1],
                high_p[t0:t1],
                low_p[t0:t1],
                close_p[t0:t1],
                sign=sign,
            )

    return pd.Series(estimates, index=df_proc.index, name=f"EDGE_rolling_{window}")