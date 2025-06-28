"""
Expanding window EDGE estimator implementation.

This module provides an expanding window implementation of the EDGE estimator,
ensuring compatibility with all pandas windowing features like 'step'.

Author: Jakub Polec
Date: 2025-06-28

Part of the QuantJourney framework - The framework with advanced quantitative 
finance tools and insights.
"""
import warnings
import numpy as np
import pandas as pd
from .edge import edge as edge_single # Import the core, fast estimator

def edge_expanding(
    df: pd.DataFrame,
    min_periods: int = 3,
    sign: bool = False,
) -> pd.Series:
    """
    Computes expanding EDGE estimates by calling the core estimator on a growing window.
    """
    if min_periods < 3:
        warnings.warn("min_periods < 3 is not recommended, setting to 3.", UserWarning)
        min_periods = 3
        
    # --- 1. Data Preparation ---
    df_proc = df.rename(columns=str.lower).copy()
    open_p = df_proc["open"].values
    high_p = df_proc["high"].values
    low_p = df_proc["low"].values
    close_p = df_proc["close"].values

    n = len(df_proc)
    estimates = np.full(n, np.nan)

    # --- 2. Loop and Apply ---
    # This loop perfectly replicates the test's logic for an expanding window.
    for i in range(n):
        t1 = i + 1
        if t1 >= min_periods:
            estimates[i] = edge_single(
                open_p[:t1],
                high_p[:t1],
                low_p[:t1],
                close_p[:t1],
                sign=sign,
            )
            
    return pd.Series(estimates, index=df_proc.index, name="EDGE_expanding")
