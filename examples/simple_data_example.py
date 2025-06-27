#!/usr/bin/env python3
"""
Simple Data Fetcher Example

Demonstrates the basic usage of the simplified data fetcher for
fetching stock data, crypto data, and BTC websocket streams.
"""

import asyncio
import sys
import os
import pandas as pd
import matplotlib.pyplot as plt

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data.fetch import DataFetcher, get_stock_data, get_crypto_data, stream_btc_data
from quantjourney_bidask import edge

async def main():
    print("=" * 50)
    print("Simple Data Fetcher Example")
    print("=" * 50)
    
    # Initialize data fetcher
    fetcher = DataFetcher()
    
    # Example 1: Fetch stock data
    print("\n1. Fetching stock data (AAPL)...")
    stock_data = get_stock_data("AAPL", period="5d")
    print(f"Stock data shape: {stock_data.shape}")
    if not stock_data.empty:
        print("Stock data sample:")
        print(stock_data.head())
        
        # Calculate bid-ask spread estimate for stock
        if len(stock_data) > 1:
            spread_estimate = edge(stock_data['open'], stock_data['high'], 
                                 stock_data['low'], stock_data['close'])
            print(f"Estimated bid-ask spread: {spread_estimate:.6f}")
    
    # Example 2: Fetch crypto historical data  
    print("\n2. Fetching crypto historical data (BTC/USDT)...")
    crypto_data = await get_crypto_data("BTC/USDT", "binance", "1h", 24)
    print(f"Crypto data shape: {crypto_data.shape}")
    print("Crypto data sample:")
    print(crypto_data.head())
    
    if len(crypto_data) > 1:
        spread_estimate = edge(crypto_data['open'], crypto_data['high'], 
                             crypto_data['low'], crypto_data['close'])
        print(f"Estimated BTC bid-ask spread: {spread_estimate:.6f}")
    
    # Example 3: Stream BTC data (synthetic for demo)
    print("\n3. Streaming BTC data for 10 seconds...")
    btc_stream = await fetcher.get_btc_1m_websocket(duration_seconds=10)
    print(f"BTC stream data shape: {btc_stream.shape}")
    print("BTC stream sample:")
    print(btc_stream.head())
    
    if not btc_stream.empty:
        print(f"Average spread during stream: {btc_stream['spread'].mean():.2f}")
        print(f"Average spread %: {(btc_stream['spread'] / btc_stream['price']).mean() * 100:.4f}%")
    
    # Example 4: Save and load data
    print("\n4. Testing data save/load...")
    if not crypto_data.empty:
        filepath = fetcher.save_data(crypto_data, "btc_sample_data")
        print(f"Data saved to: {filepath}")
        
        loaded_data = fetcher.load_data("btc_sample_data")
        print(f"Loaded data shape: {loaded_data.shape}")
    
    # Example 5: Create a simple plot
    print("\n5. Creating simple visualization...")
    
    if not crypto_data.empty:
        plt.figure(figsize=(12, 8))
        
        # Plot 1: Price chart
        plt.subplot(2, 1, 1)
        plt.plot(crypto_data['timestamp'], crypto_data['close'], 
                label='BTC Close Price', color='orange', linewidth=2)
        plt.title('BTC Price (Last 24 Hours)')
        plt.ylabel('Price (USDT)')
        plt.legend()
        plt.grid(True, alpha=0.3)
        
        # Plot 2: Volume
        plt.subplot(2, 1, 2)
        plt.bar(crypto_data['timestamp'], crypto_data['volume'], 
               alpha=0.7, color='blue', width=0.02)
        plt.title('BTC Volume')
        plt.ylabel('Volume')
        plt.xlabel('Time')
        plt.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig('_output/simple_data_example.png', dpi=150, bbox_inches='tight')
        plt.show()
        
        print("Chart saved to _output/simple_data_example.png")
    
    # Example 6: Stream data with real-time plotting
    if not btc_stream.empty:
        plt.figure(figsize=(10, 6))
        plt.plot(range(len(btc_stream)), btc_stream['price'], 
                'o-', color='orange', linewidth=2, markersize=4)
        plt.title('BTC Price Stream (10 seconds)')
        plt.ylabel('Price (USDT)')
        plt.xlabel('Time (seconds)')
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        plt.savefig('_output/btc_stream_example.png', dpi=150, bbox_inches='tight')
        plt.show()
        
        print("Stream chart saved to _output/btc_stream_example.png")
    
    print("\n" + "=" * 50)
    print("Example completed successfully!")
    print("=" * 50)

if __name__ == "__main__":
    # Ensure output directory exists
    os.makedirs("_output", exist_ok=True)
    
    # Run the example
    asyncio.run(main())