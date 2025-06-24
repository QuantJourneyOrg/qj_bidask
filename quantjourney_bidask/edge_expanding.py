import pandas as pd
from typing import Union
from .edge import edge
from .edge_rolling import edge_rolling

def edge_expanding(
    df: pd.DataFrame,
    min_periods: int = 1,
    sign: bool = False
) -> pd.Series:
    """
    Compute expanding window estimates of the bid-ask spread from OHLC prices.

    Uses the efficient estimator from Ardia, Guidotti, & Kroencke (2024):
    https://doi.org/10.1016/j.jfineco.2024.103916. Calculates spreads over
    expanding windows starting from the first observation.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame with columns 'open', 'high', 'low', 'close' (case-insensitive).
    min_periods : int, default 1
        Minimum number of observations required for an estimate. Note that
        at least 3 observations are needed for a non-NaN result.
    sign : bool, default False
        If True, returns signed estimates. If False, returns absolute values.

    Returns
    -------
    pd.Series
        Series of expanding spread estimates, indexed by the DataFrame's index.
        A value of 0.01 corresponds to a 1% spread. NaN for periods with
        insufficient data.

    Notes
    -----
    - The function leverages `edge_rolling` with a window equal to the DataFrame length.
    - Missing values are handled automatically.
    - The estimator is most reliable with sufficient data (e.g., 20+ observations).

    Examples
    --------
    >>> import pandas as pd
    >>> df = pd.read_csv("https://raw.githubusercontent.com/eguidotti/bidask/main/pseudocode/ohlc.csv")
    >>> spreads = edge_expanding(df, min_periods=21)
    >>> print(spreads.head())
    """
    # Standardize column names
    df = df.rename(columns=str.lower).copy()
    required_cols = ['open', 'high', 'low', 'close']
    if not all(col in df.columns for col in required_cols):
        raise ValueError("DataFrame must contain 'open', 'high', 'low', 'close' columns")

    return edge_rolling(
        df=df,
        window=len(df),
        min_periods=max(min_periods, 3),
        sign=sign
    )