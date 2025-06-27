
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from quantjourney_bidask import edge_rolling
from data.fetch import get_stock_data




# Fetch Yahoo Finance data
yf_df = get_stock_data("AAPL", period="3mo", interval="1d")

# Apply liquidity risk monitor
aapl_df = liquidity_risk_monitor(yf_df, window=20, spread_zscore_threshold=1.5)

# Plot
plt.figure(figsize=(12, 8))

# Spread plot
plt.subplot(2, 1, 1)
plt.plot(aapl_df['timestamp'], aapl_df['spread'] * 100, label='Spread (%)', color='blue')
plt.scatter(
    aapl_df[aapl_df['risk_flag']]['timestamp'],
    aapl_df[aapl_df['risk_flag']]['spread'] * 100,
    color='red', label='High Risk', marker='x'
)
plt.title('AAPL Bid-Ask Spread with Liquidity Risk Flags (Daily, 20d Window)')
plt.xlabel('Date')
plt.ylabel('Spread (%)')
plt.legend()

# Z-score plot
plt.subplot(2, 1, 2)
plt.plot(aapl_df['timestamp'], aapl_df['spread_zscore'], label='Spread Z-Score', color='green')
plt.axhline(y=1.5, color='red', linestyle='--', label='Threshold')
plt.title('Spread Z-Score')
plt.xlabel('Date')
plt.ylabel('Z-Score')
plt.legend()

plt.tight_layout()
plt.show()

# Print high-risk periods
print("High Liquidity Risk Periods for AAPL:")
print(aapl_df[aapl_df['risk_flag']][['timestamp', 'spread', 'spread_zscore']])