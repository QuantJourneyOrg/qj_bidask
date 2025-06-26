#!/usr/bin/env python3
"""
Spread Monitoring Example

Demonstrates real-time monitoring of bid-ask spreads with threshold alerts.
"""

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

from quantjourney_bidask import edge_rolling, fetch_yfinance_data




def spread_monitor(df, window=24, low_percentile=25, high_percentile=75):
    """
    Monitor bid-ask spreads relative to historical percentiles.
    
    Parameters
    ----------
    df : pd.DataFrame
        DataFrame with OHLC columns and 'timestamp', 'symbol'.
    window : int
        Rolling window size for spread estimation.
    low_percentile : float
        Percentile for low spread threshold (e.g., 25 for 25th percentile).
    high_percentile : float
        Percentile for high spread threshold (e.g., 75 for 75th percentile).
    
    Returns
    -------
    pd.DataFrame
        DataFrame with additional columns: 'spread', 'low_threshold',
        'high_threshold', 'spread_status' ('low', 'normal', 'high').
    """
    df = df.copy()
    df['spread'] = edge_rolling(df, window=window)
    
    # Compute rolling percentiles for thresholds
    df['low_threshold'] = df['spread'].rolling(window=window*2, min_periods=window).quantile(low_percentile / 100)
    df['high_threshold'] = df['spread'].rolling(window=window*2, min_periods=window).quantile(high_percentile / 100)
    
    # Assign status
    df['spread_status'] = 'normal'
    df.loc[df['spread'] <= df['low_threshold'], 'spread_status'] = 'low'
    df.loc[df['spread'] >= df['high_threshold'], 'spread_status'] = 'high'
    
    return df

print("Spread Monitor Example")
print("=====================")

# Generate synthetic data for demonstration
print("\n1. Creating synthetic market data...")
np.random.seed(42)
n = 200
base_price = 100

# Simulate varying volatility
volatility = 0.02 * (1 + 0.5 * np.sin(np.linspace(0, 4*np.pi, n)))
returns = np.random.normal(0, volatility)
prices = base_price * np.exp(np.cumsum(returns))

# Simulate varying spreads (higher during volatile periods)
spread_base = 0.005  # 0.5% base spread
spread_multiplier = 1 + 0.8 * volatility / 0.02  # Higher spread during high volatility
spread_pct = spread_base * spread_multiplier

# Create OHLC data
open_prices = prices
high_prices = prices * (1 + np.random.uniform(0, spread_pct/2, n))
low_prices = prices * (1 - np.random.uniform(0, spread_pct/2, n))
close_prices = prices + np.random.normal(0, 0.001, n)

synthetic_df = pd.DataFrame({
    'open': open_prices,
    'high': high_prices,
    'low': low_prices,
    'close': close_prices,
    'timestamp': pd.date_range('2024-01-01', periods=n, freq='30min'),
    'symbol': 'SYNTHETIC'
})

print(f"Generated {len(synthetic_df)} synthetic observations")

# Apply spread monitor
print("\n2. Applying spread monitoring...")
monitored_df = spread_monitor(synthetic_df, window=24, low_percentile=25, high_percentile=75)

# Create visualization
print("\n3. Creating visualization...")
fig, axes = plt.subplots(3, 1, figsize=(14, 12))

# Price plot
axes[0].plot(monitored_df['timestamp'], monitored_df['close'], label='Close Price', color='black')
axes[0].set_title('Synthetic Asset Price')
axes[0].set_ylabel('Price')
axes[0].legend()
axes[0].grid(True, alpha=0.3)

# Spread monitoring plot
axes[1].plot(monitored_df['timestamp'], monitored_df['spread'] * 100, 
             label='Spread (%)', color='blue', linewidth=1.5)
axes[1].plot(monitored_df['timestamp'], monitored_df['low_threshold'] * 100, 
             label='Low Threshold (25th)', color='green', linestyle='--', alpha=0.8)
axes[1].plot(monitored_df['timestamp'], monitored_df['high_threshold'] * 100, 
             label='High Threshold (75th)', color='red', linestyle='--', alpha=0.8)

# Color-code points by status
for status, color in [('low', 'green'), ('normal', 'blue'), ('high', 'red')]:
    mask = monitored_df['spread_status'] == status
    if mask.any():
        axes[1].scatter(
            monitored_df[mask]['timestamp'],
            monitored_df[mask]['spread'] * 100,
            color=color,
            label=f'{status.capitalize()} Spread',
            alpha=0.7,
            s=20
        )

axes[1].set_title('Spread Monitoring with Alert Thresholds')
axes[1].set_ylabel('Spread (%)')
axes[1].legend()
axes[1].grid(True, alpha=0.3)

# Status timeline
status_colors = {'low': 'green', 'normal': 'blue', 'high': 'red'}
status_numeric = monitored_df['spread_status'].map({'low': 0, 'normal': 1, 'high': 2})
axes[2].scatter(monitored_df['timestamp'], status_numeric, 
                c=[status_colors[s] for s in monitored_df['spread_status']], 
                alpha=0.7, s=30)
axes[2].set_title('Spread Status Timeline')
axes[2].set_ylabel('Status')
axes[2].set_xlabel('Time')
axes[2].set_yticks([0, 1, 2])
axes[2].set_yticklabels(['Low', 'Normal', 'High'])
axes[2].grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('spread_monitor_results.png', dpi=150, bbox_inches='tight')
print("Plot saved as 'spread_monitor_results.png'")
plt.show()

# Summary statistics
print("\n4. Monitoring Summary:")
status_counts = monitored_df['spread_status'].value_counts()
total_obs = len(monitored_df)
print(f"Total observations: {total_obs}")
for status in ['low', 'normal', 'high']:
    count = status_counts.get(status, 0)
    pct = count / total_obs * 100
    print(f"{status.capitalize()} spread periods: {count} ({pct:.1f}%)")

# Alert examples
high_spread_periods = monitored_df[monitored_df['spread_status'] == 'high']
if len(high_spread_periods) > 0:
    print(f"\nHigh spread alerts ({len(high_spread_periods)} periods):")
    for _, row in high_spread_periods.head().iterrows():
        print(f"  {row['timestamp']}: {row['spread']*100:.3f}% (threshold: {row['high_threshold']*100:.3f}%)")

# Real data example
print("\n5. Real data example...")
try:
    # Fetch real data
    real_df = fetch_yfinance_data(
        tickers=["QQQ"],  # NASDAQ ETF
        period="2mo", 
        interval="1h"
    )
    
    # Apply monitoring
    real_monitored = spread_monitor(real_df, window=24, low_percentile=20, high_percentile=80)
    
    # Simple plot
    plt.figure(figsize=(12, 6))
    plt.plot(real_monitored['timestamp'], real_monitored['spread'] * 10000, 
             label='QQQ Spread (bps)', alpha=0.8)
    plt.plot(real_monitored['timestamp'], real_monitored['high_threshold'] * 10000, 
             label='High Threshold (80th)', color='red', linestyle='--')
    
    # Highlight high spread periods
    high_periods = real_monitored[real_monitored['spread_status'] == 'high']
    if len(high_periods) > 0:
        plt.scatter(high_periods['timestamp'], high_periods['spread'] * 10000,
                   color='red', label='High Spread Alert', s=30, alpha=0.8)
    
    plt.title('QQQ Real-Time Spread Monitoring (Hourly)')
    plt.xlabel('Date')
    plt.ylabel('Spread (basis points)')
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig('qqq_spread_monitor.png', dpi=150, bbox_inches='tight')
    print("QQQ monitoring plot saved as 'qqq_spread_monitor.png'")
    plt.show()
    
    print(f"\nQQQ monitoring results:")
    print(f"Mean spread: {real_monitored['spread'].mean()*10000:.2f} bps")
    print(f"High spread alerts: {len(high_periods)} periods")
    
except Exception as e:
    print(f"Could not fetch real data: {e}")

print("\nSpread monitoring example completed!")