import numpy as np
import pandas as pd
from typing import Union, Dict
from .edge import edge

def edge_rolling(
    df: pd.DataFrame,
    window: Union[int, str, pd.offsets.BaseOffset],
    sign: bool = False,
    **kwargs
) -> pd.Series:
    """
    Compute rolling window estimates of the bid-ask spread from OHLC prices.

    Uses the efficient estimator from Ardia, Guidotti, & Kroencke (2024):
    https://doi.org/10.1016/j.jfineco.2024.103916. Optimized for fast computation
    over rolling windows using vectorized operations.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame with columns 'open', 'high', 'low', 'close' (case-insensitive).
    window : int, str, or pd.offsets.BaseOffset
        Size of the rolling window. Can be an integer (number of periods),
        a string (e.g., '30D' for 30 days), or a pandas offset object.
        See pandas.DataFrame.rolling for details.
    sign : bool, default False
        If True, returns signed estimates. If False, returns absolute values.
    **kwargs
        Additional arguments to pass to pandas.DataFrame.rolling, such as
        min_periods, step, or center.

    Returns
    -------
    pd.Series
        Series of rolling spread estimates, indexed by the DataFrame's index.
        A value of 0.01 corresponds to a 1% spread. NaN for periods with
        insufficient data.

    Notes
    -----
    - The function accounts for missing values by masking invalid periods.
    - The first observation is masked due to the need for lagged prices.
    - For large datasets, this implementation is significantly faster than
      applying `edge` repeatedly over windows.

    Examples
    --------
    >>> import pandas as pd
    >>> df = pd.read_csv("https://raw.githubusercontent.com/eguidotti/bidask/main/pseudocode/ohlc.csv")
    >>> spreads = edge_rolling(df, window=21)
    >>> print(spreads.head())
    """
    # Standardize column names
    df = df.rename(columns=str.lower).copy()
    required_cols = ['open', 'high', 'low', 'close']
    if not all(col in df.columns for col in required_cols):
        raise ValueError("DataFrame must contain 'open', 'high', 'low', 'close' columns")

    # Compute log-prices, handling non-positive prices by replacing them with NaN
    # This prevents errors from taking log of zero or negative values
    o = np.log(df['open'].where(df['open'] > 0))  # Log of open prices
    h = np.log(df['high'].where(df['high'] > 0))  # Log of high prices  
    l = np.log(df['low'].where(df['low'] > 0))    # Log of low prices
    c = np.log(df['close'].where(df['close'] > 0)) # Log of close prices
    m = (h + l) / 2.0  # Log of geometric mid-price each period

    # Get lagged (previous period) log-prices using pandas shift
    # These are needed to compute overnight returns and indicators
    h1 = h.shift(1)  # Previous period's high
    l1 = l.shift(1)  # Previous period's low 
    c1 = c.shift(1)  # Previous period's close
    m1 = m.shift(1)  # Previous period's mid-price

    # Compute log-returns:
    r1 = m - o        # Mid-price minus open (intraday return from open to mid)
    r2 = o - m1       # Open minus previous mid (overnight return from prev mid to open) 
    r3 = m - c1       # Mid-price minus previous close (return from prev close to mid)
    r4 = c1 - m1      # Previous close minus previous mid (prev intraday return from mid to close)
    r5 = o - c1       # Open minus previous close (overnight return from prev close to open)

    # Compute indicator variables for price variation and extremes
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

    # Compute base products needed for rolling means
    # Products of log-returns for covariance calculations
    r12 = r1 * r2  # Mid-Open × Open-PrevMid
    r15 = r1 * r5  # Mid-Open × Open-PrevClose
    r34 = r3 * r4  # Mid-PrevClose × PrevClose-PrevMid
    r45 = r4 * r5  # PrevClose-PrevMid × Open-PrevClose
    
    # Products with tau indicator for valid periods
    tr1 = tau * r1  # Scaled Mid-Open
    tr2 = tau * r2  # Scaled Open-PrevMid
    tr4 = tau * r4  # Scaled PrevClose-PrevMid
    tr5 = tau * r5  # Scaled Open-PrevClose

    # Set up DataFrame for efficient rolling mean calculations
    # Includes all products needed for moment conditions and variance calculations
    x = pd.DataFrame({
        # Basic return products
        'r12': r12, 'r34': r34, 'r15': r15, 'r45': r45, 
        'tau': tau,  # Price variation indicator
        # Individual returns
        'r1': r1, 'tr2': tr2, 'r3': r3, 'tr4': tr4, 'r5': r5,
        # Squared terms for variance
        'r12_sq': r12**2, 'r34_sq': r34**2, 'r15_sq': r15**2, 'r45_sq': r45**2,
        # Cross products for covariance
        'r12_r34': r12 * r34, 'r15_r45': r15 * r45,
        # Products with tau-scaled returns
        'tr2_r2': tr2 * r2, 'tr4_r4': tr4 * r4, 'tr5_r5': tr5 * r5,
        'tr2_r12': tr2 * r12, 'tr4_r34': tr4 * r34,
        'tr5_r15': tr5 * r15, 'tr4_r45': tr4 * r45,
        'tr4_r12': tr4 * r12, 'tr2_r34': tr2 * r34,
        'tr2_r4': tr2 * r4, 'tr1_r45': tr1 * r45,
        'tr5_r45': tr5 * r45, 'tr4_r5': tr4 * r5,
        'tr5': tr5,
        # Extreme price indicators
        'po1': po1, 'po2': po2, 'pc1': pc1, 'pc2': pc2
    }, index=df.index)

    # Handle first observation and adjust window parameters
    x.iloc[0] = np.nan  # Mask first row due to lagged values
    if isinstance(window, (int, np.integer)):
        window = max(0, window - 1)  # Adjust window size for lag
    if 'min_periods' in kwargs and isinstance(kwargs['min_periods'], (int, np.integer)):
        kwargs['min_periods'] = max(0, kwargs['min_periods'] - 1)

    # Compute rolling means for all variables
    m = x.rolling(window=window, **kwargs).mean()

    # Calculate probabilities of price extremes
    pt = m['tau']  # Probability of valid price variation
    po = m['po1'] + m['po2']  # Probability of open being extreme
    pc = m['pc1'] + m['pc2']  # Probability of close being extreme

    # Mask periods with insufficient data or zero probabilities
    nt = x['tau'].rolling(window=window, **kwargs).sum()
    m[(nt < 2) | (po == 0) | (pc == 0)] = np.nan

    # Compute coefficients for moment conditions
    a1 = -4.0 / po  # Scaling for open price moments
    a2 = -4.0 / pc  # Scaling for close price moments
    a3 = m['r1'] / pt  # Mean-adjustment for Mid-Open
    a4 = m['tr4'] / pt  # Mean-adjustment for PrevClose-PrevMid
    a5 = m['r3'] / pt  # Mean-adjustment for Mid-PrevClose
    a6 = m['r5'] / pt  # Mean-adjustment for Open-PrevClose
    
    # Pre-compute squared and product terms
    a12 = 2 * a1 * a2
    a11 = a1**2
    a22 = a2**2
    a33 = a3**2
    a55 = a5**2
    a66 = a6**2

    # Calculate moment condition expectations
    e1 = a1 * (m['r12'] - a3 * m['tr2']) + a2 * (m['r34'] - a4 * m['r3'])  # First moment
    e2 = a1 * (m['r15'] - a3 * m['tr5']) + a2 * (m['r45'] - a4 * m['r5'])  # Second moment

    # Calculate variances of moment conditions
    # v1: Variance of first moment condition
    v1 = -e1**2 + (
        a11 * (m['r12_sq'] - 2 * a3 * m['tr2_r12'] + a33 * m['tr2_r2']) +
        a22 * (m['r34_sq'] - 2 * a5 * m['tr4_r34'] + a55 * m['tr4_r4']) +
        a12 * (m['r12_r34'] - a3 * m['tr2_r34'] - a5 * m['tr4_r12'] + a3 * a5 * m['tr2_r4'])
    )
    # v2: Variance of second moment condition
    v2 = -e2**2 + (
        a11 * (m['r15_sq'] - 2 * a3 * m['tr5_r15'] + a33 * m['tr5_r5']) +
        a22 * (m['r45_sq'] - 2 * a6 * m['tr4_r45'] + a66 * m['tr4_r4']) +
        a12 * (m['r15_r45'] - a3 * m['tr5_r45'] - a6 * m['tr1_r45'] + a3 * a6 * m['tr4_r5'])
    )

    # Compute squared spread using optimal GMM weights
    vt = v1 + v2  # Total variance
    s2 = pd.Series(np.where(
        vt > 0,
        (v2 * e1 + v1 * e2) / vt,  # Optimal weighted average if variance is positive
        (e1 + e2) / 2.0  # Simple average if variance is zero/negative
    ), index=df.index)

    # Compute signed root
    s = np.sqrt(np.abs(s2))
    if sign:
        s *= np.sign(s2)

    return pd.Series(s, index=df.index, name=f"EDGE_rolling_{window}")