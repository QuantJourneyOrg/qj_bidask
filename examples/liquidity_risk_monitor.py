import pandas as pd
import matplotlib.pyplot as plt
from quantjourney_bidask import edge_rolling
from data.fetch import fetch_binance_data

def liquidity_risk_monitor(df, window=24, spread_zscore_threshold=2):
    """
    Monitor liquidity risk by flagging periods with high bid-ask spread z-scores.
    
    Parameters
    ----------
    df : pd.DataFrame
        DataFrame with OHLC columns and 'timestamp', 'symbol'.
    window : int
        Rolling window size for spread estimation (in periods).
    spread_zscore_threshold : float
        Z-score threshold for flagging high liquidity risk.
    
    Returns
    -------
    pd.DataFrame
        DataFrame with additional columns: 'spread', 'spread_zscore', 'risk_flag'.
    """
    df = df.copy()
    df['spread'] = edge_rolling(df, window=window)
    df['spread_zscore'] = (df['spread'] - df['spread'].mean()) / df['spread'].std()
    df['risk_flag'] = df['spread_zscore'] > spread_zscore_threshold
    return df

# Fetch Binance data
binance_df = fetch_binance_data(
    symbols=["BTCUSDT"],
    timeframe="1h",
    start="2024-01-01T00:00:00Z",
    end="2024-01-07T00:00:00Z",
    api_key="your-api-key"
)

# Apply liquidity risk monitor
btc_df = liquidity_risk_monitor(binance_df, window=24, spread_zscore_threshold=2)

# Plot
plt.figure(figsize=(12, 8))

# Plot spreads
plt.subplot(2, 1, 1)
plt.plot(btc_df['timestamp'], btc_df['spread'] * 100, label='Spread (%)', color='blue')
plt.scatter(
    btc_df[btc_df['risk_flag']]['timestamp'],
    btc_df[btc_df['risk_flag']]['spread'] * 100,
    color='red', label='High Risk', marker='x'
)
plt.title('BTCUSDT Bid-Ask Spread with Liquidity Risk Flags (1h, 24h Window)')
plt.xlabel('Timestamp')
plt.ylabel('Spread (%)')
plt.legend()

# Plot z-scores
plt.subplot(2, 1, 2)
plt.plot(btc_df['timestamp'], btc_df['spread_zscore'], label='Spread Z-Score', color='green')
plt.axhline(y=2, color='red', linestyle='--', label='Threshold')
plt.title('Spread Z-Score')
plt.xlabel('Timestamp')
plt.ylabel('Z-Score')
plt.legend()

plt.tight_layout()
plt.show()

# Print high-risk periods
high_risk = btc_df[btc_df['risk_flag']][['timestamp', 'spread', 'spread_zscore']]
print("High Liquidity Risk Periods:")
print(high_risk)