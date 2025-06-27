#!/usr/bin/env python3
"""
Cryptocurrency Spread Comparison

Compares bid-ask spreads across different cryptocurrency pairs to analyze
liquidity differences and trading costs.
"""

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import sys
sys.path.insert(0, './data')
from quantjourney_bidask import edge_rolling
from data.fetch import DataFetcher, get_crypto_data


def create_synthetic_crypto_data():
    """
    Create synthetic cryptocurrency data with realistic spread characteristics.
    
    Returns
    -------
    Dict[str, pd.DataFrame]
        Dictionary mapping crypto symbols to their OHLC data
    """
    np.random.seed(42)
    n = 200  # Number of observations
    
    # Define crypto characteristics based on real market observations
    crypto_configs = {
        'BTC': {
            'name': 'Bitcoin',
            'base_price': 45000,
            'base_spread_bps': 2,    # 2 basis points (very liquid)
            'volatility': 0.03,
            'volume_factor': 1.0,
            'color': '#F7931E'
        },
        'ETH': {
            'name': 'Ethereum', 
            'base_price': 2800,
            'base_spread_bps': 4,    # 4 basis points
            'volatility': 0.04,
            'volume_factor': 0.8,
            'color': '#627EEA'
        },
        'ADA': {
            'name': 'Cardano',
            'base_price': 0.45,
            'base_spread_bps': 15,   # 15 basis points (less liquid)
            'volatility': 0.06,
            'volume_factor': 0.3,
            'color': '#0033AD'
        },
        'DOGE': {
            'name': 'Dogecoin',
            'base_price': 0.08,
            'base_spread_bps': 25,   # 25 basis points (meme coin, higher spread)
            'volatility': 0.08,
            'volume_factor': 0.4,
            'color': '#C2A633'
        }
    }
    
    crypto_data = {}
    
    for symbol, config in crypto_configs.items():
        print(f"Generating {config['name']} ({symbol}) data...")
        
        # Generate price series with varying volatility
        volatility = config['volatility'] * (1 + 0.5 * np.sin(np.linspace(0, 4*np.pi, n)))
        returns = np.random.normal(0, volatility)
        prices = config['base_price'] * np.exp(np.cumsum(returns))
        
        # Generate spread that correlates with volatility and inverse volume
        volatility_impact = np.abs(returns) / config['volatility']
        volume_sim = np.random.gamma(2, config['volume_factor'], n)  # Simulated volume
        volume_impact = 1 / np.sqrt(volume_sim)  # Higher volume = lower spread
        
        spread_multiplier = 1 + 2 * volatility_impact + volume_impact
        spread_bps = config['base_spread_bps'] * spread_multiplier
        spread_fraction = spread_bps / 10000
        
        # Create OHLC data with embedded spreads
        open_prices = prices
        high_prices = prices * (1 + np.random.uniform(0, spread_fraction, n))
        low_prices = prices * (1 - np.random.uniform(0, spread_fraction, n))
        close_prices = prices + np.random.normal(0, config['base_price'] * 0.0001, n)
        
        # Ensure OHLC consistency
        for i in range(n):
            high_prices[i] = max(high_prices[i], open_prices[i], close_prices[i])
            low_prices[i] = min(low_prices[i], open_prices[i], close_prices[i])
        
        df = pd.DataFrame({
            'timestamp': pd.date_range('2024-01-01', periods=n, freq='1h'),
            'symbol': symbol,
            'open': open_prices,
            'high': high_prices,
            'low': low_prices,
            'close': close_prices,
            'volume': volume_sim * 1e6,  # Scale to realistic volume
            'config': [config] * n  # Store config for later use
        })
        
        crypto_data[symbol] = df
    
    return crypto_data

def analyze_spread_patterns(crypto_data):
    """
    Analyze spread patterns across different cryptocurrencies.
    
    Parameters
    ----------
    crypto_data : Dict[str, pd.DataFrame]
        Dictionary of crypto OHLC data
    
    Returns
    -------
    Dict[str, pd.DataFrame]
        Dictionary with spread analysis results
    """
    analysis_results = {}
    
    for symbol, df in crypto_data.items():
        print(f"Analyzing {symbol} spreads...")
        
        # Calculate spreads with different windows
        df['spread_5min'] = edge_rolling(df, window=5)   # 5-hour window
        df['spread_24h'] = edge_rolling(df, window=24)   # 24-hour window
        df['spread_7d'] = edge_rolling(df, window=168)   # 7-day window (168 hours)
        
        # Convert to basis points
        for col in ['spread_5min', 'spread_24h', 'spread_7d']:
            df[f'{col}_bps'] = df[col] * 10000
        
        # Calculate additional metrics
        df['price_volatility'] = df['close'].rolling(24).std() / df['close'].rolling(24).mean()
        df['volume_ma'] = df['volume'].rolling(24).mean()
        
        analysis_results[symbol] = df
    
    return analysis_results

def create_spread_comparison_plots(analysis_results):
    """
    Create comprehensive spread comparison visualizations.
    """
    print("Creating spread comparison visualizations...")
    
    # Main comparison plot
    fig = plt.figure(figsize=(20, 12))
    
    # Plot 1: Price Evolution (normalized)
    ax1 = plt.subplot(2, 3, 1)
    for symbol, df in analysis_results.items():
        config = df['config'].iloc[0]
        normalized_price = df['close'] / df['close'].iloc[0]
        ax1.plot(df['timestamp'], normalized_price, label=f"{config['name']}", 
                color=config['color'], linewidth=2)
    ax1.set_title('Normalized Price Evolution')
    ax1.set_ylabel('Price (Normalized)')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # Plot 2: 24h Rolling Spreads
    ax2 = plt.subplot(2, 3, 2)
    for symbol, df in analysis_results.items():
        config = df['config'].iloc[0]
        valid_data = df.dropna(subset=['spread_24h_bps'])
        ax2.plot(valid_data['timestamp'], valid_data['spread_24h_bps'], 
                label=f"{config['name']}", color=config['color'], linewidth=2)
    ax2.set_title('24h Rolling Spreads')
    ax2.set_ylabel('Spread (basis points)')
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    
    # Plot 3: Spread Distribution
    ax3 = plt.subplot(2, 3, 3)
    spread_data = []
    labels = []
    colors = []
    for symbol, df in analysis_results.items():
        config = df['config'].iloc[0]
        valid_spreads = df['spread_24h_bps'].dropna()
        if len(valid_spreads) > 0:
            spread_data.append(valid_spreads)
            labels.append(config['name'])
            colors.append(config['color'])
    
    box_plot = ax3.boxplot(spread_data, labels=labels, patch_artist=True)
    for patch, color in zip(box_plot['boxes'], colors):
        patch.set_facecolor(color)
        patch.set_alpha(0.7)
    ax3.set_title('Spread Distribution (24h Window)')
    ax3.set_ylabel('Spread (basis points)')
    ax3.tick_params(axis='x', rotation=45)
    ax3.grid(True, alpha=0.3)
    
    # Plot 4: Spread vs Volatility
    ax4 = plt.subplot(2, 3, 4)
    for symbol, df in analysis_results.items():
        config = df['config'].iloc[0]
        valid_data = df.dropna(subset=['spread_24h_bps', 'price_volatility'])
        if len(valid_data) > 10:
            ax4.scatter(valid_data['price_volatility'] * 100, valid_data['spread_24h_bps'],
                       alpha=0.6, color=config['color'], label=config['name'], s=20)
    ax4.set_title('Spread vs Price Volatility')
    ax4.set_xlabel('Price Volatility (%)')
    ax4.set_ylabel('Spread (basis points)')
    ax4.legend()
    ax4.grid(True, alpha=0.3)
    
    # Plot 5: Average Daily Spread Pattern
    ax5 = plt.subplot(2, 3, 5)
    for symbol, df in analysis_results.items():
        config = df['config'].iloc[0]
        df['hour'] = df['timestamp'].dt.hour
        hourly_spreads = df.groupby('hour')['spread_24h_bps'].mean()
        ax5.plot(hourly_spreads.index, hourly_spreads.values, 
                marker='o', label=config['name'], color=config['color'], linewidth=2)
    ax5.set_title('Average Spread by Hour of Day')
    ax5.set_xlabel('Hour of Day')
    ax5.set_ylabel('Average Spread (bps)')
    ax5.legend()
    ax5.grid(True, alpha=0.3)
    
    # Plot 6: Cumulative Spread Costs
    ax6 = plt.subplot(2, 3, 6)
    for symbol, df in analysis_results.items():
        config = df['config'].iloc[0]
        valid_data = df.dropna(subset=['spread_24h_bps'])
        if len(valid_data) > 0:
            # Simulate cumulative trading costs (assuming 1 trade per hour)
            cumulative_cost = valid_data['spread_24h_bps'].cumsum() / 2  # Half spread per trade
            ax6.plot(valid_data['timestamp'], cumulative_cost, 
                    label=config['name'], color=config['color'], linewidth=2)
    ax6.set_title('Cumulative Trading Costs')
    ax6.set_xlabel('Time')
    ax6.set_ylabel('Cumulative Cost (bps)')
    ax6.legend()
    ax6.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('crypto_spread_comprehensive_analysis.png', dpi=150, bbox_inches='tight')
    print("Comprehensive analysis saved as 'crypto_spread_comprehensive_analysis.png'")
    plt.show()

def print_spread_statistics(analysis_results):
    """
    Print detailed spread statistics for all cryptocurrencies.
    """
    print("\n" + "="*80)
    print("CRYPTOCURRENCY SPREAD ANALYSIS SUMMARY")
    print("="*80)
    
    # Summary statistics table
    print(f"\n{'Asset':<10} {'Mean (bps)':<12} {'Std (bps)':<12} {'Min (bps)':<12} {'Max (bps)':<12} {'Median (bps)':<12}")
    print("-" * 70)
    
    summary_data = []
    for symbol, df in analysis_results.items():
        config = df['config'].iloc[0]
        valid_spreads = df['spread_24h_bps'].dropna()
        
        if len(valid_spreads) > 0:
            stats = {
                'symbol': symbol,
                'name': config['name'],
                'mean': valid_spreads.mean(),
                'std': valid_spreads.std(),
                'min': valid_spreads.min(),
                'max': valid_spreads.max(),
                'median': valid_spreads.median(),
                'count': len(valid_spreads)
            }
            summary_data.append(stats)
            
            print(f"{config['name']:<10} {stats['mean']:<12.2f} {stats['std']:<12.2f} "
                  f"{stats['min']:<12.2f} {stats['max']:<12.2f} {stats['median']:<12.2f}")
    
    # Ranking by liquidity (lower spread = higher liquidity)
    print(f"\n{'LIQUIDITY RANKING (Lower spread = Higher liquidity)'}")
    print("-" * 50)
    sorted_cryptos = sorted(summary_data, key=lambda x: x['mean'])
    for i, crypto in enumerate(sorted_cryptos, 1):
        print(f"{i}. {crypto['name']:<15} (Avg: {crypto['mean']:.2f} bps)")
    
    # Trading cost analysis
    print(f"\n{'TRADING COST ANALYSIS (Round-trip costs)'}")
    print("-" * 50)
    print("Assuming $10,000 trade size:")
    for crypto in sorted_cryptos:
        cost_per_trade = 10000 * crypto['mean'] / 10000  # Cost in dollars
        print(f"{crypto['name']:<15}: ${cost_per_trade:.2f} per round-trip trade")
    
    # Volatility vs Spread correlation
    print(f"\n{'SPREAD-VOLATILITY CORRELATION'}")
    print("-" * 40)
    for symbol, df in analysis_results.items():
        config = df['config'].iloc[0]
        valid_data = df.dropna(subset=['spread_24h_bps', 'price_volatility'])
        if len(valid_data) > 10:
            correlation = valid_data['spread_24h_bps'].corr(valid_data['price_volatility'])
            print(f"{config['name']:<15}: {correlation:.3f}")

def create_live_comparison_example():
    """
    Example of how to set up live comparison monitoring.
    """
    print("\n" + "="*60)
    print("LIVE COMPARISON SETUP EXAMPLE")
    print("="*60)
    
    example_code = '''
# Example: Live Multi-Crypto Spread Monitoring
from quantjourney_bidask import LiveSpreadMonitor

def setup_live_comparison():
    """Set up live monitoring for multiple crypto pairs."""
    
    # Define crypto pairs to monitor
    symbols = ['BTCUSDT', 'ETHUSDT', 'ADAUSDT', 'DOGEUSDT']
    
    # Create monitor with 20-minute rolling window
    monitor = LiveSpreadMonitor(symbols, window=20)
    
    # Set different alert thresholds based on expected liquidity
    monitor.set_alert_threshold('BTCUSDT', high_bps=10, low_bps=1)
    monitor.set_alert_threshold('ETHUSDT', high_bps=15, low_bps=2)
    monitor.set_alert_threshold('ADAUSDT', high_bps=30, low_bps=5)
    monitor.set_alert_threshold('DOGEUSDT', high_bps=50, low_bps=8)
    
    # Add comparison callback
    def comparison_callback(candle_data, spread_data):
        symbol = spread_data['symbol'].upper()
        spread_bps = spread_data['spread_bps']
        
        # Log to database or file for later analysis
        print(f"{symbol}: {spread_bps:.2f}bps")
    
    def alert_callback(alert_data):
        # Send alerts via email, Slack, etc.
        print(f"ALERT: {alert_data['symbol'].upper()} spread "
              f"{alert_data['type'].lower()}: {alert_data['spread_bps']:.2f}bps")
    
    monitor.add_data_callback(comparison_callback)
    monitor.add_alert_callback(alert_callback)
    
    return monitor

# Usage:
# monitor = setup_live_comparison()
# monitor.start()
    '''
    
    print(example_code)

if __name__ == "__main__":
    print("Cryptocurrency Spread Comparison Analysis")
    print("========================================")
    
    # Generate synthetic crypto data
    print("\n1. Generating synthetic cryptocurrency data...")
    crypto_data = create_synthetic_crypto_data()
    
    # Analyze spread patterns
    print("\n2. Analyzing spread patterns...")
    analysis_results = analyze_spread_patterns(crypto_data)
    
    # Create visualizations
    print("\n3. Creating comparison visualizations...")
    create_spread_comparison_plots(analysis_results)
    
    # Print statistics
    print("\n4. Statistical analysis...")
    print_spread_statistics(analysis_results)
    
    # Show live monitoring example
    print("\n5. Live monitoring setup...")
    create_live_comparison_example()
    
    print("\n" + "="*80)
    print("ANALYSIS COMPLETE")
    print("="*80)
    print("Key Insights:")
    print("• Bitcoin (BTC) typically has the tightest spreads due to high liquidity")
    print("• Altcoins generally have wider spreads, especially during volatile periods")
    print("• Spread correlates positively with price volatility")
    print("• Trading costs vary significantly across different crypto assets")
    print("• Real-time monitoring helps identify optimal trading windows")
    print("\nFiles generated:")
    print("• crypto_spread_comprehensive_analysis.png - Complete visual analysis")
    print("\nFor live monitoring, see the LiveSpreadMonitor class example above.")